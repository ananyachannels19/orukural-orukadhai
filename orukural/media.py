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


def loudness(path: Path) -> dict:
    """Integrated loudness (LUFS), true peak (dBTP), loudness range and threshold, from ffmpeg's loudnorm."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
                          "loudnorm=print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    j = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return {"lufs": float(j["input_i"]), "true_peak": float(j["input_tp"]), "lra": float(j["input_lra"]),
            "thresh": float(j["input_thresh"])}


def normalize_loudness(path: Path, lufs: float = -14.0, true_peak: float = -1.0, kbps: int = 192) -> dict:
    """Two-pass loudnorm of a finished video's sound, in place (the picture is copied). Returns the result."""
    m = loudness(path)
    tmp = path.with_name(path.stem + ".loud" + path.suffix)
    run(["-i", str(path), "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af",
         f"loudnorm=I={lufs}:TP={true_peak}:LRA=11:measured_I={m['lufs']}:measured_TP={m['true_peak']}"
         f":measured_LRA={m['lra']}:measured_thresh={m['thresh']}:linear=true,aresample=48000,"
         f"alimiter=limit={10 ** ((true_peak - 0.3) / 20):.4f}:level=disabled",
         "-c:a", "aac", "-b:a", f"{kbps}k", "-ar", "48000", "-movflags", "+faststart", str(tmp)])
    tmp.replace(path)
    return loudness(path)


def frozen(path: Path, seconds: float = 0.3, noise_db: int = -60) -> list[tuple[float, float]]:
    """(start, end) of every stretch where the picture does not change for `seconds` or more (a held frame)."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:v", "-vf",
                          f"freezedetect=n={noise_db}dB:d={seconds}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x.split("freeze_start:")[1].split()[0]) for x in err.splitlines() if "freeze_start:" in x]
    ends = [float(x.split("freeze_end:")[1].split()[0]) for x in err.splitlines() if "freeze_end:" in x]
    return [(a, ends[i] if i < len(ends) else duration(path)) for i, a in enumerate(starts)]


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return bool(out.strip())


def pauses(path: Path, min_seconds: float = 0.15, noise_db: int = -35, af: str = "") -> list[tuple[float, float]]:
    """(start, end) of every quiet stretch in an audio file, from ffmpeg's silencedetect (af: filters first)."""
    chain = f"{af}," if af else ""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af",
                          f"{chain}silencedetect=noise={noise_db}dB:d={min_seconds}", "-f", "null", "-"],
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


def median_pitch(path: Path, frames: int = 60) -> float | None:
    """Typical voice pitch (Hz) of a speech file, YIN-style on up to `frames` voiced 50 ms frames.
    Grown men speak around 85-155 Hz, women and children around 165-300 Hz."""
    import array
    import statistics
    sr, w = 8000, 200
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = array.array("h", raw)
    starts = [i for i in range(0, len(x) - 2 * w, w)
              if sum(v * v for v in x[i:i + w:4]) / (w / 4) > 1000 ** 2]
    step = max(1, len(starts) // frames)
    found = []
    for i in starts[::step]:
        fr = x[i:i + 2 * w]
        d = [sum((fr[j] - fr[j + tau]) ** 2 for j in range(w)) for tau in range(sr // 400, sr // 60)]
        run, cm = 0.0, []
        for k, v in enumerate(d, 1):
            run += v
            cm.append(v * k / run if run else 1.0)
        k = next((k for k in range(len(cm) - 1) if cm[k] < 0.15 and cm[k] <= cm[k + 1]), None)
        if k is not None:
            found.append(sr / (k + sr // 400))
    return round(statistics.median(found)) if len(found) >= 5 else None


def silence(path: Path, seconds: float) -> None:
    run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{seconds:.3f}", "-c:a", "libmp3lame", "-q:a", "4", str(path)])


def fill_frame(scale: float = 1.0) -> str:
    """Scale-and-crop filter that fills a 1080x1920 frame, optionally punched in (lanczos: sharpest upscale)."""
    w, h = int(W * scale), int(H * scale)
    return f"scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
