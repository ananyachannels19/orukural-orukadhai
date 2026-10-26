"""Small FFmpeg helpers shared by the voice, visuals and assembly steps."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

W, H = 1080, 1920


def require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} not found. Install FFmpeg (macOS: brew install ffmpeg).")


def run(args: list[str]) -> None:
    proc = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {' '.join(args)}\n{proc.stderr[-2000:]}")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return float(json.loads(out)["format"]["duration"])


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return bool(out.strip())


def pauses(path: Path, min_seconds: float = 0.15, noise_db: int = -35) -> list[tuple[float, float]]:
    """(start, end) of every quiet stretch in an audio file, from ffmpeg's silencedetect."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                          f"silencedetect=noise={noise_db}dB:d={min_seconds}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    out, start = [], None
    for line in err.splitlines():
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].split()[0])
        elif "silence_end:" in line and start is not None:
            out.append((max(0.0, start), float(line.split("silence_end:")[1].split()[0])))
            start = None
    if start is not None:
        out.append((start, duration(path)))
    return out


def silence(path: Path, seconds: float) -> None:
    run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{seconds:.3f}", "-c:a", "libmp3lame", "-q:a", "4", str(path)])


def fill_frame(scale: float = 1.0) -> str:
    """Scale-and-crop filter that fills a 1080x1920 frame, optionally punched in."""
    w, h = int(W * scale), int(H * scale)
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
