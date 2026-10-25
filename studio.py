#!/usr/bin/env python3
"""orukural-studio command line.

Phase 1 commands:
  python studio.py data build            rebuild data/kurals.json from the public sources
  python studio.py status                counts by status, and the next kurals in line
  python studio.py plan [-n 3]           which kurals the next run will make
  python studio.py script 301 [--dry-run] [--force]
  python studio.py script-check 301      re-check a hand-edited episodes/K0301/script.json
  python studio.py spend [K0301]         spend log

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

    sp = sub.add_parser("spend")
    sp.add_argument("episode", nargs="?")
    sp.set_defaults(fn=cmd_spend)

    args = p.parse_args(argv)
    dry = args.dry_run or getattr(args, "sub_dry_run", None)
    s = config.load(dry_run=True if dry else None)
    return args.fn(s, args) or 0


if __name__ == "__main__":
    sys.exit(main())
