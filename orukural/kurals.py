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

    def adhikaram_sequence(self, order: list[int]) -> list[int]:
        rest = [a for a in range(1, 134) if a not in order]
        return list(order) + rest

    def next_planned(self, order: list[int], count: int) -> list[dict]:
        """Next `count` planned kurals, finishing the current adhikaram before starting another."""
        picked = []
        for adh in self.adhikaram_sequence(order):
            for k in self.adhikaram(adh):
                if k["status"] == "planned":
                    picked.append(k)
                    if len(picked) == count:
                        return picked
        return picked

    def after(self, kural: dict, order: list[int]) -> dict | None:
        """The kural that follows this one in production order (for the 'next kural' tease)."""
        seq = [k for adh in self.adhikaram_sequence(order) for k in self.adhikaram(adh)]
        idx = next(i for i, k in enumerate(seq) if k["number"] == kural["number"])
        return seq[idx + 1] if idx + 1 < len(seq) else None


def verse_text(k: dict, sep: str = "\n") -> str:
    return f"{k['verse']['line1']}{sep}{k['verse']['line2']}"
