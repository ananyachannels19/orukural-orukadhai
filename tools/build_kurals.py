"""Build data/kurals.json from two independent public datasets and cross-check them.

The verses themselves (c. 1st century) are public domain. We take ONLY the verse
text, numbering and chapter structure from the sources. The modern commentaries
bundled in those datasets (Mu. Varadarasanar, Solomon Pappaiah, Kalaignar, etc.)
are deliberately NOT copied: meanings in kurals.json are written by us, per
episode, in our own words.

Sources (downloaded into data/sources/, which is gitignored):
  A  github.com/tk120404/thirukkural          thirukkural.json + detail.json
  B  pypi.org/project/thirukkural  (v1.1)     kural.db (sqlite)

Every kural where A and B disagree (after normalising spaces/punctuation) must
have an entry in data/verse_overrides.yaml, or the build fails.

Re-running the build keeps per-kural working fields (status, meanings, episode
ids) from an existing kurals.json.
"""

from __future__ import annotations

import io
import json
import re
import sqlite3
import sys
import unicodedata
import zipfile
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "sources"
OUT = ROOT / "data" / "kurals.json"

A_KURALS = "https://raw.githubusercontent.com/tk120404/thirukkural/master/thirukkural.json"
A_DETAIL = "https://raw.githubusercontent.com/tk120404/thirukkural/master/detail.json"
B_WHEEL = (
    "https://files.pythonhosted.org/packages/61/fe/"
    "bae24bdbc27908ed4a8bbb35f27579cc4b891cb86ad43d0db94f1aeb547a/thirukkural-1.1-py3-none-any.whl"
)

# Parimelazhagar's traditional division into iyals (sections inside each paal).
IYALS = [
    (1, 4, "பாயிரவியல்"), (5, 24, "இல்லறவியல்"), (25, 37, "துறவறவியல்"), (38, 38, "ஊழியல்"),
    (39, 63, "அரசியல்"), (64, 95, "அங்கவியல்"), (96, 108, "ஒழிபியல்"),
    (109, 115, "களவியல்"), (116, 133, "கற்பியல்"),
]
PAALS = {
    1: ("அறத்துப்பால்", "Virtue", 1, 38),
    2: ("பொருட்பால்", "Wealth", 39, 108),
    3: ("காமத்துப்பால்", "Love", 109, 133),
}
WORK_FIELDS = ("status", "meaning_ta", "meaning_en", "episode_id", "youtube_id", "instagram_id", "notes")


def fetch(url: str, dest: Path) -> Path:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def load_sources():
    a_json = json.loads(fetch(A_KURALS, SRC / "tk120404_thirukkural.json").read_text("utf-8"))
    a_detail = json.loads(fetch(A_DETAIL, SRC / "tk120404_detail.json").read_text("utf-8"))
    db = SRC / "thirukkural_cl_kural.db"
    if not db.exists():
        whl = requests.get(B_WHEEL, timeout=60)
        whl.raise_for_status()
        db.write_bytes(zipfile.ZipFile(io.BytesIO(whl.content)).read("thirukkural/kural.db"))
    con = sqlite3.connect(db)
    b_rows = {
        r[0]: {"verse": r[1], "adhikaram_en": r[2].strip()}
        for r in con.execute("select no, kural_ta, adigaaram_en from kural")
    }
    a_rows = {k["Number"]: k for k in a_json["kural"]}
    chapters = {}
    for paal in a_detail[0]["section"]["detail"]:
        for iyal in paal["chapterGroup"]["detail"]:
            for ch in iyal["chapters"]["detail"]:
                chapters[ch["number"]] = ch["name"].strip()
    return a_rows, b_rows, chapters


def norm(s: str) -> str:
    return re.sub(r"[\s.,;:!?'\"‘’“”/]+", "", unicodedata.normalize("NFC", s))


def clean_line(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s)).strip()


def seers(line1: str, line2: str) -> tuple[int, int]:
    return len(line1.split()), len(line2.split())


def has_stray_chars(s: str) -> bool:
    # Tamil block letters, spaces and light punctuation only; Tamil digits are never in a verse.
    return bool(re.search(r"[^ஂ-்ௗ\s.,;:!?'\-]", s))


def build() -> list[dict]:
    a_rows, b_rows, chapters = load_sources()
    overrides = yaml.safe_load((ROOT / "data" / "verse_overrides.yaml").read_text("utf-8")) or {}
    themes = yaml.safe_load((ROOT / "data" / "themes.yaml").read_text("utf-8"))
    old = {}
    if OUT.exists():
        old = {k["number"]: k for k in json.loads(OUT.read_text("utf-8"))}

    assert len(a_rows) == 1330 and len(b_rows) == 1330, "both sources must have 1330 kurals"
    problems, out = [], []
    for n in range(1, 1331):
        a = a_rows[n]
        a_text = f"{a['Line1']} {a['Line2']}"
        b_text = b_rows[n]["verse"]
        agree = norm(a_text) == norm(b_text)
        if n in overrides:
            ov = overrides[n]
            line1, line2 = clean_line(ov["line1"]), clean_line(ov["line2"])
            check = f"override:{ov['chosen']}" + (" (needs review)" if ov.get("review") else "")
        elif agree:
            line1, line2 = clean_line(a["Line1"]), clean_line(a["Line2"])
            check = "sources_agree"
            b1, b2 = (clean_line(x) for x in b_text.split("\n", 1))
            if seers(line1, line2) != (4, 3) and seers(b1, b2) == (4, 3):
                line1, line2 = b1, b2  # same letters, B keeps the 4 + 3 seer layout
        else:
            problems.append(f"#{n}: sources disagree and no override\n  A: {a_text}\n  B: {b_text}")
            continue
        if has_stray_chars(line1 + line2):
            problems.append(f"#{n}: unexpected characters in {line1!r} / {line2!r}")

        adh = (n - 1) // 10 + 1
        paal_no = next(p for p, v in PAALS.items() if v[2] <= adh <= v[3])
        iyal = next(name for lo, hi, name in IYALS if lo <= adh <= hi)
        rec = {
            "number": n,
            "id": f"K{n:04d}",
            "verse": {"line1": line1, "line2": line2},
            "transliteration": {
                "line1": a.get("transliteration1", "").strip(),
                "line2": a.get("transliteration2", "").strip(),
            },
            "adhikaram": {
                "number": adh,
                "name_ta": chapters[adh],
                "name_en": b_rows[n]["adhikaram_en"],
                "position": (n - 1) % 10 + 1,
            },
            "paal": {"number": paal_no, "name_ta": PAALS[paal_no][0], "name_en": PAALS[paal_no][1]},
            "iyal": iyal,
            "theme": themes[adh],
            "verse_check": check,
            "status": "planned",
            "meaning_ta": None,
            "meaning_en": None,
            "episode_id": None,
            "youtube_id": None,
            "instagram_id": None,
            "notes": None,
        }
        if n in old:
            for f in WORK_FIELDS:
                if old[n].get(f) is not None:
                    rec[f] = old[n][f]
        out.append(rec)

    layout = [k["number"] for k in out if seers(**k["verse"]) != (4, 3)]
    if layout:
        print(f"note: verses not laid out as 4 + 3 seers (display only): {layout}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(f"{len(problems)} problem(s); fix data/verse_overrides.yaml")
    return out


def main() -> None:
    kurals = build()
    OUT.write_text(json.dumps(kurals, ensure_ascii=False, indent=1) + "\n", "utf-8")
    agree = sum(k["verse_check"] == "sources_agree" for k in kurals)
    review = [k["number"] for k in kurals if "needs review" in k["verse_check"]]
    print(f"wrote {OUT.relative_to(ROOT)}: {len(kurals)} kurals, {agree} identical in both sources, "
          f"{len(kurals) - agree} resolved by override; flagged for human review: {review}")


if __name__ == "__main__":
    main()
