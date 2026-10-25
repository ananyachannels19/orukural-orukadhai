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
  python studio.py characters [--force]  generate Thatha/Kavin reference images (once; commit them)
  python studio.py voice 301             narration, one file per segment
  python studio.py flow-sheet 301        what to make in Google Flow, and where to save it
  python studio.py voice-test            one kural line in 8 Tamil voices → review/voice_test/
  python studio.py visuals 301 [--shots 2,5]   collect (Flow) or make (Gemini) stills and clips
  python studio.py assemble 301          cut and mix → episodes/K0301/render/K0301_draft.mp4
  python studio.py render 301            voice + visuals + assemble in one go

Add --dry-run to any command to run it without paid API calls.
"""

from __future__ import annotations

import argparse
import collections
import subprocess
import sys

from orukural import config
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
    sheet = visuals.flow_sheet(s, ep_dir, sc, k["id"])
    kinds = [j["kind"] for j in sheet["jobs"]]
    print(f"{ep_dir.relative_to(s.root)}/flow/README.md: {kinds.count('character_ref')} character refs, "
          f"{kinds.count('image')} images, {kinds.count('clip')} clips ({sheet['clip_credits']} of "
          f"{sheet['daily_credits']} daily credits)")


def cmd_voice_test(s, args):
    from orukural import voice
    name, cfg = voice.provider_cfg(s)
    voices = args.voices.split(",") if args.voices else [
        f"ta-IN-Chirp3-HD-{v}" for v in ("Charon", "Iapetus", "Puck", "Orus", "Kore", "Aoede", "Leda", "Sulafat")
    ] if name == "google_tts" else [cfg["voice_id"]]
    outs = voice.voice_test(s, args.text, voices, s.root / "review" / "voice_test")
    for o in outs:
        print(o.relative_to(s.root))


def cmd_characters(s, args):
    from orukural import visuals
    for cid, path in visuals.character_refs(s, force=args.force).items():
        print(f"{cid}: {path.relative_to(s.root)}")


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
    fs.set_defaults(fn=cmd_flow_sheet)

    vt = sub.add_parser("voice-test", help="say one line in several voices to pick one by ear")
    vt.add_argument("--text", default="செல்லிடத்துக் காப்பான் சினங்காப்பான் அல்லிடத்துக் காக்கின்என் காவாக்கா லென்?")
    vt.add_argument("--voices", help="comma-separated voice names")
    vt.set_defaults(fn=cmd_voice_test)

    ch = sub.add_parser("characters", help="generate the character reference images")
    ch.add_argument("--force", action="store_true")
    ch.set_defaults(fn=cmd_characters)

    for name, fn in (("voice", cmd_voice), ("visuals", cmd_visuals), ("assemble", cmd_assemble), ("render", cmd_render)):
        c = sub.add_parser(name)
        c.add_argument("kural")
        c.add_argument("--force", action="store_true", help="ignore the cache and pay again")
        c.add_argument("--shots", help="visuals only: comma-separated shot numbers to (re)make")
        c.add_argument("--dry-run", action="store_true", default=None, dest="sub_dry_run")
        c.set_defaults(fn=fn)

    sp = sub.add_parser("spend")
    sp.add_argument("episode", nargs="?")
    sp.set_defaults(fn=cmd_spend)

    args = p.parse_args(argv)
    dry = args.dry_run or getattr(args, "sub_dry_run", None)
    s = config.load(dry_run=True if dry else None)
    return args.fn(s, args) or 0


if __name__ == "__main__":
    sys.exit(main())
