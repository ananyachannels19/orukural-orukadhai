"""Cost guard and asset cache.

Every paid call goes through `Ledger.run()`:
  1. If a cached result exists for the same inputs, return it and spend nothing.
  2. Refuse the call if the episode's logged spend plus the estimate would pass the cap.
  3. Run it, cache the result, and log the real cost to logs/spend.jsonl.
A failed call is never cached, so it can be retried; a successful one is never re-run
unless the caller passes force=True.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class BudgetExceeded(RuntimeError):
    pass


def cache_key(payload: Any) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


@dataclass
class CallResult:
    value: Any
    cost_usd: float
    cached: bool
    key: str


class Ledger:
    def __init__(self, ledger_path: Path, cache_dir: Path, per_episode_cap: float):
        self.ledger_path = ledger_path
        self.cache_dir = cache_dir
        self.cap = per_episode_cap

    def entries(self) -> list[dict]:
        if not self.ledger_path.exists():
            return []
        return [json.loads(line) for line in self.ledger_path.read_text("utf-8").splitlines() if line.strip()]

    def spent(self, episode_id: str) -> float:
        return round(sum(e["cost_usd"] for e in self.entries() if e["episode_id"] == episode_id), 4)

    def _log(self, entry: dict) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def run(
        self,
        *,
        episode_id: str,
        step: str,
        inputs: Any,
        estimate_usd: float,
        call: Callable[[], tuple[Any, float, dict]],
        force: bool = False,
    ) -> CallResult:
        """`call` returns (json-serialisable value, real cost in USD, extra log fields)."""
        key = cache_key({"step": step, "inputs": inputs})
        cached = self.cache_dir / step / f"{key}.json"
        if cached.exists() and not force:
            return CallResult(json.loads(cached.read_text("utf-8")), 0.0, True, key)

        spent = self.spent(episode_id)
        if spent + estimate_usd > self.cap:
            raise BudgetExceeded(
                f"{episode_id}: {step} would take spend to ~${spent + estimate_usd:.2f}, "
                f"over the ${self.cap:.2f} per-episode cap (already ${spent:.2f})"
            )

        started = time.time()
        value, cost, extra = call()
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(value, ensure_ascii=False, indent=1), "utf-8")
        self._log({
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "episode_id": episode_id,
            "step": step,
            "cost_usd": round(cost, 5),
            "seconds": round(time.time() - started, 1),
            "cache_key": key,
            **extra,
        })
        return CallResult(value, cost, False, key)
