"""Load config.yaml and .env into one settings object."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def _truthy(value: str | None) -> bool | None:
    if value is None or value.strip() == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    raw: dict[str, Any]
    root: Path
    dry_run: bool
    review_gate: bool

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def path(self, key: str) -> Path:
        return self.root / self.raw["paths"][key]

    def file(self, key: str) -> Path:
        return self.root / self.raw[key]


def load(config_path: Path | None = None, dry_run: bool | None = None) -> Settings:
    root = (config_path.parent if config_path else ROOT).resolve()
    load_dotenv(root / ".env", override=False)
    raw = yaml.safe_load((config_path or root / "config.yaml").read_text("utf-8"))
    env_dry = _truthy(os.environ.get("DRY_RUN"))
    env_gate = _truthy(os.environ.get("REVIEW_GATE"))
    return Settings(
        raw=raw,
        root=root,
        dry_run=dry_run if dry_run is not None else (env_dry if env_dry is not None else bool(raw.get("dry_run"))),
        review_gate=env_gate if env_gate is not None else bool(raw.get("review_gate", True)),
    )
