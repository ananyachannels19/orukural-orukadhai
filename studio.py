#!/usr/bin/env python3
"""orukural-studio command line.

Phase 1 commands:
  python studio.py data build            rebuild data/kurals.json from the public sources
  python studio.py status                counts by status, and the next kurals in line
  python studio.py plan [-n 3]           which kurals the next run will make
  python studio.py script 301 [--dry-run] [--force]
  python studio.py script-check 301      re-check a hand-edited episodes/K0301/script.json
  python studio.py spend [K0301]         spend log

Phase 2 commands:
  python studio.py refs 301 [--force]    make missing character/place/prop references (Gemini or dry-run)
  python studio.py continuity-sheet 301  contact sheets + review file for the continuity check
  python studio.py voice 301             narration, one file per segment
  python studio.py flow-sheet 301        what to make in Google Flow, and where to save it
  python studio.py voice-test            one kural line in 8 Tamil voices → review/voice_test/
  python studio.py visuals 301 [--shots 2,5]   collect (Flow) or make (Gemini) stills and clips
  python studio.py assemble 301          cut and mix → episodes/K0301/render/K0301_draft.mp4
  python studio.py render 301            voice + visuals + assemble in one go

Studio Live:
  python studio.py live                  live dashboard of every step on http://localhost:8765
  python studio.py event 301 clips done --shot 2 --credits 12 --detail "Shot 2 clip made"
                                         log a step (used by the Flow session on the Mac)

Add --dry-run to any command to run it without paid API calls.
"""

from __future__ import annotations

import argparse
import collections
import subprocess
import sys

from orukural import brewlibs, config, live
from orukural.kurals import STATUSES, KuralStore, verse_text
from orukural.ledger import Ledger


def cmd_data(s, args):
    if args.action == "build":
        subprocess.run([sys.executable, str(s.root / "tools" / "build_kurals.py")], check=True)


def cmd_status(s, args):
    store = KuralStore(s.path("kurals"))
    counts = collections.Counter(k["status"] for k in store.items)
    for st in STATUSES:
        print(f"{st:>10}: {counts.get(st, 0)}")
    print(f"\nreview gate: {'on' if s.review_gate else 'off'} · dry run: {'on' if s.dry_run else 'off'}")
    cmd_plan(s, argparse.Namespace(n=3))


def cmd_plan(s, args):
    store = KuralStore(s.path("kurals"))
    print("next up:")
    for k in store.next_planned(s["adhikaram_order"], args.n):
        a = k["adhikaram"]
        print(f"  #{k['number']:>4}  {a['name_ta']} ({a['name_en']}) {a['position']}/10 · {k['theme']}")
        print("         " + verse_text(k, " / "))


def _report(res):
    k = res["kural"]
    if res.get("session"):
        print(f"#{k['number']}: prompt written. {res['next']}")
        return 0
    tag = " [dry run]" if res.get("dry_run") else ""
    cost = "" if res.get("dry_run") or "cost" not in res else (" · cached, $0" if res.get("cached") else f" · ${res['cost']:.3f}")
    print(f"#{k['number']} → {res['dir'].relative_to(res['dir'].parents[1])}/script.md{tag}{cost}")
    for e in res["errors"]:
        print(f"  ERROR  {e}")
    for w in res["warnings"]:
        print(f"  warn   {w}")
    return 1 if res["errors"] else 0


def cmd_script(s, args):
    from orukural import scriptgen
    store = KuralStore(s.path("kurals"))
    rc = 0
    for ref in args.kurals:
        rc |= _report(scriptgen.generate(s, store, ref, force=args.force))
    return rc


def cmd_script_check(s, args):
    from orukural import scriptgen
    store = KuralStore(s.path("kurals"))
    return _report(scriptgen.revalidate(s, store, args.kural))


def _episode(s, ref):
    import json
    from orukural.schema import EpisodeScript
    store = KuralStore(s.path("kurals"))
    k = store.get(ref)
    ep_dir = s.path("episodes") / k["id"]
    f = ep_dir / "script.json"
    if not f.exists():
        raise SystemExit(f"no script for #{k['number']}; run `studio.py script {k['number']}` first")
    payload = json.loads(f.read_text("utf-8"))
    if payload.get("errors"):
        raise SystemExit(f"{k['id']} script has errors; fix them and run script-check first")
    # Dry runs work in their own subfolder so placeholders never mix with real assets.
    work = ep_dir / "dryrun" if s.dry_run else ep_dir
    return k, work, EpisodeScript.model_validate(payload["script"])


def cmd_flow_sheet(s, args):
    from orukural import visuals
    k, ep_dir, sc = _episode(s, args.kural)
    pool = s["flow"]["monthly_top_up_per_episode"] if args.use_monthly else 0
    sheet = visuals.flow_sheet(s, ep_dir, sc, k["id"], pool=pool)
    kinds = [j["kind"] for j in sheet["jobs"]]
    extra = f", {sheet['monthly_credits_used']} of them monthly" if sheet["monthly_credits_used"] else ""
    refs = sum(kinds.count(x) for x in ("character_ref", "location_ref", "prop_ref"))
    print(f"{ep_dir.relative_to(s.root)}/flow/README.md: {refs} references, "
          f"{kinds.count('image')} images, {kinds.count('clip')} clips: {sheet['clip_credits']} credits over "
          f"{sheet['clip_days']} day(s){extra}")


def cmd_voice_test(s, args):
    from orukural import voice
    name, cfg = voice.provider_cfg(s)
    voices = args.voices.split(",") if args.voices else [
        f"ta-IN-Chirp3-HD-{v}" for v in ("Charon", "Iapetus", "Puck", "Orus", "Kore", "Aoede", "Leda", "Sulafat")
    ] if name == "google_tts" else [
        "Charon", "Iapetus", "Puck", "Orus", "Kore", "Aoede", "Algieba", "Sulafat"
    ] if name == "gemini_tts" else [cfg["voice_id"]]
    outs = voice.voice_test(s, args.text, voices, s.root / "review" / "voice_test")
    for o in outs:
        print(o.relative_to(s.root))


def cmd_refs(s, args):
    from orukural import continuity, visuals
    k, ep_dir, sc = _episode(s, args.kural)
    if s["images"]["provider"] == "flow" and not s.dry_run:
        raise SystemExit(f"images.provider is flow: run `studio.py flow-sheet {args.kural}` and make them in Flow")
    visuals.ensure_refs(s, ep_dir, sc, force=args.force)
    for shot in sc.shots:
        print(f"shot {shot.n}: " + ", ".join(f"{lab} ({p.name})" for lab, p in continuity.shot_refs(s, ep_dir, sc, shot)))


def cmd_continuity_sheet(s, args):
    from orukural import continuity
    k, ep_dir, sc = _episode(s, args.kural)
    for p in continuity.contact_sheet(s, ep_dir, sc, ep_dir / "flow" / "review"):
        print(p.relative_to(s.root))
    review = continuity.load_review(ep_dir)
    for kind in ("images", "clips"):
        gaps = continuity.review_gaps(sc, review, kind)
        print(f"{kind}: " + ("all pass" if not gaps else "; ".join(gaps)))


def cmd_voice(s, args):
    from orukural import voice
    k, ep_dir, sc = _episode(s, args.kural)
    m = voice.generate(s, ep_dir, sc, k["id"], force=args.force)
    for seg in m["segments"]:
        lo, hi = seg["planned"]
        flag = "  ← longer than planned" if seg["seconds"] > hi - lo + 0.3 else ""
        print(f"  {seg['file']:<22} {seg['seconds']:5.2f}s (planned {hi - lo:.1f}s){flag}")
    cost = "dry run" if m["dry_run"] else f"${m['cost_usd']:.3f}"
    print(f"voice: {cost}")


def cmd_visuals(s, args):
    from orukural import visuals
    k, ep_dir, sc = _episode(s, args.kural)
    only = {int(x) for x in args.shots.split(",")} if args.shots else None
    m = visuals.generate(s, ep_dir, sc, k["id"], force=args.force, only=only)
    print(f"animated shots: {m['animated']}")
    for sh in m["shots"]:
        print(f"  shot {sh['n']:>2}: {sh['image']}" + (f" + {sh['clip']}" if sh["clip"] else " (pan/zoom)"))


def cmd_assemble(s, args):
    from orukural import assemble
    k, ep_dir, sc = _episode(s, args.kural)
    t = assemble.assemble(s, ep_dir, sc, k["id"])
    note = "" if t["within_target"] else "  ← outside the 35–45 s target"
    print(f"{ep_dir.relative_to(s.root)}/render/{t['output']}: {t['total_seconds']:.1f}s{note}"
          f" · music: {t['music'] or 'none (add files to assets/music)'}")
    if not t["dry_run"] and k["status"] in ("planned", "scripted"):
        store = KuralStore(s.path("kurals"))
        store.set(k["number"], status="rendered")
        store.save()


def cmd_render(s, args):
    cmd_voice(s, args)
    cmd_visuals(s, args)
    cmd_assemble(s, args)
    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])
    k = KuralStore(s.path("kurals")).get(args.kural)
    print(f"episode spend so far: ${ledger.spent(k['id']):.2f} of ${ledger.cap:.2f}")


def cmd_spend(s, args):
    ledger = Ledger(s.path("ledger"), s.path("cache"), s["budget"]["per_episode_cap"])
    rows = [e for e in ledger.entries() if not args.episode or e["episode_id"] == args.episode]
    by_ep = collections.defaultdict(float)
    for e in rows:
        by_ep[e["episode_id"]] += e["cost_usd"]
        print(f"{e['ts']}  {e['episode_id']}  {e['step']:<8} ${e['cost_usd']:.4f}  {e.get('model', '')}")
    print("\n" + "\n".join(f"{ep}: ${v:.3f} of ${ledger.cap:.2f}" for ep, v in sorted(by_ep.items())) if by_ep
          else "no spend logged yet")


def cmd_live(s, args):
    live.serve(s, args.host, args.port, open_browser=not args.no_browser)


def cmd_event(s, args):
    store = KuralStore(s.path("kurals"))
    e = live.emit(s, store.get(args.kural)["id"], args.stage, args.status, args.detail or "",
                  shot=args.shot, attempt=args.attempt, credits=args.credits, credits_left=args.credits_left,
                  requests=args.requests, seconds=args.seconds)
    print(e or "could not write logs/events.jsonl")


def main(argv=None):
    p = argparse.ArgumentParser(prog="studio.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", default=None, help="no paid API calls")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("data")
    d.add_argument("action", choices=["build"])
    d.set_defaults(fn=cmd_data)

    sub.add_parser("status").set_defaults(fn=cmd_status)

    pl = sub.add_parser("plan")
    pl.add_argument("-n", type=int, default=3)
    pl.set_defaults(fn=cmd_plan)

    sc = sub.add_parser("script", help="write episode scripts for one or more kural numbers")
    sc.add_argument("kurals", nargs="+")
    sc.add_argument("--force", action="store_true", help="ignore the cache and pay for a new script")
    sc.add_argument("--dry-run", action="store_true", default=None, dest="sub_dry_run")
    sc.set_defaults(fn=cmd_script)

    ck = sub.add_parser("script-check")
    ck.add_argument("kural")
    ck.set_defaults(fn=cmd_script_check)

    fs = sub.add_parser("flow-sheet", help="list the images/clips to make in Google Flow for an episode")
    fs.add_argument("kural")
    fs.add_argument("--use-monthly", action="store_true",
                    help="top up day 1 with monthly plan credits so the episode's clips fit in one day")
    fs.set_defaults(fn=cmd_flow_sheet)

    vt = sub.add_parser("voice-test", help="say one line in several voices to pick one by ear")
    vt.add_argument("--text", default="செல்லிடத்துக் காப்பான் சினங்காப்பான் அல்லிடத்துக் காக்கின்என் காவாக்கா லென்?")
    vt.add_argument("--voices", help="comma-separated voice names")
    vt.set_defaults(fn=cmd_voice_test)

    rf = sub.add_parser("refs", help="make missing character, place and prop references (Gemini or dry-run)")
    rf.add_argument("kural")
    rf.add_argument("--force", action="store_true")
    rf.set_defaults(fn=cmd_refs)

    cs = sub.add_parser("continuity-sheet", help="contact sheets and review file for the continuity check")
    cs.add_argument("kural")
    cs.set_defaults(fn=cmd_continuity_sheet)

    for name, fn in (("voice", cmd_voice), ("visuals", cmd_visuals), ("assemble", cmd_assemble), ("render", cmd_render)):
        c = sub.add_parser(name)
        c.add_argument("kural")
        c.add_argument("--force", action="store_true", help="ignore the cache and pay again")
        c.add_argument("--shots", help="visuals only: comma-separated shot numbers to (re)make")
        c.add_argument("--dry-run", action="store_true", default=None, dest="sub_dry_run")
        c.set_defaults(fn=fn)

    lv = sub.add_parser("live", help="live dashboard of every pipeline step, served from this machine")
    lv.add_argument("--port", type=int, default=8765)
    lv.add_argument("--host", default="127.0.0.1", help="0.0.0.0 to open it from a phone on the same Wi-Fi")
    lv.add_argument("--no-browser", action="store_true")
    lv.set_defaults(fn=cmd_live)

    ev = sub.add_parser("event", help="log one step to logs/events.jsonl for the live dashboard")
    ev.add_argument("kural")
    ev.add_argument("stage", choices=[k for k, _ in live.STAGES])
    ev.add_argument("status", choices=live.STATUSES)
    ev.add_argument("--detail", help="one line a person can read: what happened, and what was done about it")
    ev.add_argument("--shot", type=int)
    ev.add_argument("--attempt", type=int)
    ev.add_argument("--credits", type=int, help="Flow credits this step spent")
    ev.add_argument("--credits-left", type=int, help="credits Flow shows as left")
    ev.add_argument("--requests", type=int, help="TTS requests this step used")
    ev.add_argument("--seconds", type=float)
    ev.set_defaults(fn=cmd_event)

    sp = sub.add_parser("spend")
    sp.add_argument("episode", nargs="?")
    sp.set_defaults(fn=cmd_spend)

    args = p.parse_args(argv)
    dry = args.dry_run or getattr(args, "sub_dry_run", None)
    s = config.load(dry_run=True if dry else None)
    return args.fn(s, args) or 0


if __name__ == "__main__":
    brewlibs.ensure(sys.argv)
    sys.exit(main())
