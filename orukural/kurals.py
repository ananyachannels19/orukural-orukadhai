"""Read and update data/kurals.json, and decide which kurals come next."""

from __future__ import annotations

import json
from pathlib import Path

STATUSES = ("planned", "scripted", "rendered", "approved", "scheduled", "posted")


class KuralStore:
    def __init__(self, path: Path):
        self.path = path
        self.items: list[dict] = json.loads(path.read_text("utf-8"))
        self.by_number = {k["number"]: k for k in self.items}

    def get(self, ref: int | str) -> dict:
        n = int(str(ref).upper().lstrip("K"))
        if n not in self.by_number:
            raise KeyError(f"no kural #{n}")
        return self.by_number[n]

    def adhikaram(self, number: int) -> list[dict]:
        return [k for k in self.items if k["adhikaram"]["number"] == number]

    def set(self, ref: int | str, **fields) -> dict:
        k = self.get(ref)
        if "status" in fields and fields["status"] not in STATUSES:
            raise ValueError(f"unknown status {fields['status']!r}")
        k.update(fields)
        return k

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.items, ensure_ascii=False, indent=1) + "\n", "utf-8")
        tmp.replace(self.path)

    def sequence(self, lineup: list[dict]) -> list[dict]:
        """Production order: the lineup's kurals first, in its order, then the rest in book order."""
        first = [self.get(x["kural"]) for x in lineup]
        picked = {k["number"] for k in first}
        return first + [k for k in self.items if k["number"] not in picked]

    def next_planned(self, lineup: list[dict], count: int) -> list[dict]:
        """Next `count` planned kurals in production order."""
        return [k for k in self.sequence(lineup) if k["status"] == "planned"][:count]


def relationship(lineup: list[dict], themes: dict, kural: dict) -> str:
    """What the story is about between its people: the lineup's tag, else the adhikaram's default."""
    picked = next((x.get("relationship") for x in lineup if x["kural"] == kural["number"]), None)
    return picked or (themes.get("relationship") or {}).get(kural["adhikaram"]["number"], "friends")


def verse_text(k: dict, sep: str = "\n") -> str:
    return f"{k['verse']['line1']}{sep}{k['verse']['line2']}"


def lineup_entry(lineup: list[dict], kural: dict) -> dict:
    return next((x for x in lineup if x["kural"] == kural["number"]), {})


def kids_specials_per_month(lineup: list[dict], per_week: int) -> list[int]:
    """How many kids' specials fall in each ~4-week block of the lineup (episodes_per_week × 4 entries)."""
    block = per_week * 4
    return [sum(1 for x in lineup[i:i + block] if x.get("special") == "kids") for i in range(0, len(lineup), block)]
