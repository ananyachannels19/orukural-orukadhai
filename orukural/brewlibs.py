"""Homebrew on Apple Silicon keeps its libraries in /opt/homebrew/lib, where dlopen doesn't look, so
Pillow can't find fribidi and can't shape Tamil. dyld reads its search path only when a process
starts, so the fix is to set it and start this same command again, once."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BREW_LIB = "/opt/homebrew/lib"


def needed() -> bool:
    return (sys.platform == "darwin" and Path(BREW_LIB, "libfribidi.0.dylib").exists()
            and BREW_LIB not in os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "").split(":"))


def ensure(argv: list[str]) -> None:
    if not needed():
        return
    paths = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "").split(":")
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join([BREW_LIB] + [p for p in paths if p])
    os.execv(sys.executable, [sys.executable] + argv)
