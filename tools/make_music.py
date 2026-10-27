#!/usr/bin/env python3
"""Compose the series' background music from scratch: a tanpura drone, a bansuri-like flute in a
Carnatic raga, and soft hand-drum, all synthesised here. Nothing is sampled or downloaded, so the
tracks are ours outright: no copyright claims, no licence, no attribution, no cost.

    python tools/make_music.py              # writes assets/music/*.m4a (one per mood below)
    python tools/make_music.py --seconds 60

Each track is a gentle bed meant to sit ~20 dB under the narration; the flute stays sparse so it
never competes with the words."""
from __future__ import annotations

import argparse
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SR = 44100

# semitones above Sa for each raga's notes (ascending), with a mood and tempo
TRACKS = {
    "mohanam_playful": {"notes": [0, 2, 4, 7, 9], "bpm": 88, "sa": 146.83, "seed": 3},    # bright, story
    "hindolam_calm": {"notes": [0, 3, 5, 8, 10], "bpm": 72, "sa": 138.59, "seed": 7},      # reflective, lesson
    "suddha_dhanyasi_warm": {"notes": [0, 3, 5, 7, 10], "bpm": 80, "sa": 155.56, "seed": 11},
}


def env(n: int, attack: float, decay: float) -> np.ndarray:
    t = np.arange(n) / SR
    return np.minimum(1.0, t / max(attack, 1e-4)) * np.exp(-t / decay)


def tanpura(seconds: float, sa: float, rng) -> np.ndarray:
    """Pa-Sa'-Sa'-Sa plucks, each a bright buzzing string (many harmonics, slow decay, slight detune)."""
    out = np.zeros(int(seconds * SR))
    cycle, k = 3.2, 0
    pitches = [sa * 1.5 / 2, sa, sa, sa / 2]  # low Pa, Sa, Sa, low Sa
    t0 = 0.0
    while t0 < seconds:
        f = pitches[k % 4]
        n = int(min(cycle * 1.6, seconds - t0) * SR)
        t = np.arange(n) / SR
        tone = np.zeros(n)
        for h in range(1, 16):  # jawari: upper harmonics bloom then fade
            amp = (1 / h) * (1 + 0.6 * np.sin(np.pi * np.clip(t / 1.4, 0, 1)) * (h > 4))
            tone += amp * np.sin(2 * np.pi * f * h * (1 + rng.normal(0, 0.0004)) * t + rng.uniform(0, 6.28))
        tone *= env(n, 0.01, 2.6)
        i = int(t0 * SR)
        out[i:i + n] += tone[: len(out) - i]
        t0 += cycle / 4
        k += 1
    return out / np.max(np.abs(out))


def flute_note(f0: float, seconds: float, slide_from: float | None, rng) -> np.ndarray:
    n = int(seconds * SR)
    t = np.arange(n) / SR
    f = np.full(n, f0)
    if slide_from:  # gamaka: glide into the note
        g = min(n, int(0.12 * SR))
        f[:g] = np.linspace(slide_from, f0, g)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.4, 0, 1)
    phase = 2 * np.cumsum(np.pi * f * vib / SR)
    tone = np.sin(phase) + 0.18 * np.sin(2 * phase) + 0.06 * np.sin(3 * phase)
    breath = rng.normal(0, 1, n)
    breath = np.convolve(breath, np.ones(30) / 30, mode="same") * 0.05
    a = np.clip(t / 0.08, 0, 1) * np.clip((seconds - t) / 0.25, 0, 1)
    return (tone + breath) * a


def melody(seconds: float, sa: float, notes: list[int], bpm: float, rng) -> np.ndarray:
    """Sparse phrases of 3-6 notes moving mostly stepwise in the raga, with rests between phrases."""
    out = np.zeros(int(seconds * SR))
    beat = 60 / bpm
    scale = [sa * 2 ** ((s + 12 * o) / 12) for o in (0, 1) for s in notes] + [sa * 4]
    t, idx, prev = 2 * beat * 4, 5, None
    while t < seconds - 4:
        for _ in range(rng.integers(3, 7)):
            idx = int(np.clip(idx + rng.choice([-2, -1, -1, 1, 1, 2]), 2, len(scale) - 2))
            d = beat * rng.choice([1, 1, 2, 2, 3])
            f = scale[idx]
            note = flute_note(f, d * 1.05, prev if prev and rng.random() < 0.5 else None, rng)
            i = int(t * SR)
            out[i:i + len(note)] += note[: max(0, len(out) - i)]
            prev, t = f, t + d
        t += beat * rng.choice([4, 6, 8])  # breathing room for the voice
        idx = rng.choice([3, 4, 5, 6])
    return out / max(1e-9, np.max(np.abs(out)))


def drum(seconds: float, bpm: float, rng) -> np.ndarray:
    """Soft mridangam-like 'thom' on 1, light 'ta' on the off-beats, in an 8-beat cycle."""
    out = np.zeros(int(seconds * SR))
    beat = 60 / bpm
    pattern = [("thom", 1.0), ("ta", 0.4), (None, 0), ("ta", 0.5), ("thom", 0.7), ("ta", 0.4), ("ta", 0.3), (None, 0)]
    t, k = 0.0, 0
    while t < seconds:
        kind, amp = pattern[k % 8]
        if kind:
            n = int(0.5 * SR)
            tt = np.arange(n) / SR
            if kind == "thom":
                f = 95 * np.exp(-tt * 3) + 70
                s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.002, 0.18)
            else:
                s = (np.sin(2 * np.pi * 420 * tt) * 0.6 + rng.normal(0, 0.4, n)) * env(n, 0.001, 0.05)
            i = int(t * SR)
            out[i:i + n] += amp * s[: max(0, len(out) - i)]
        t += beat / 2
        k += 1
    return out / max(1e-9, np.max(np.abs(out)))


def reverb(x: np.ndarray, seconds: float = 1.8, mix: float = 0.25, rng=None) -> np.ndarray:
    n = int(seconds * SR)
    ir = rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR / (seconds / 5))
    ir /= np.sqrt(np.sum(ir ** 2))
    size = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return (1 - mix) * x + mix * wet


def make(name: str, spec: dict, seconds: float, out_dir: Path) -> Path:
    rng = np.random.default_rng(spec["seed"])
    drone = tanpura(seconds, spec["sa"], rng)
    tune = melody(seconds, spec["sa"], spec["notes"], spec["bpm"], rng)
    beat = drum(seconds, spec["bpm"], rng)
    tracks = []
    for side in (0, 1):  # a little width: flute a touch left, drum a touch right
        mix = 0.55 * drone + (0.42 if side == 0 else 0.34) * tune + (0.16 if side == 1 else 0.12) * beat
        tracks.append(reverb(mix, rng=np.random.default_rng(spec["seed"] + side)))
    st = np.stack(tracks, axis=1)
    fade = np.minimum(1, np.minimum(np.arange(len(st)) / (2 * SR), (len(st) - np.arange(len(st))) / (3 * SR)))
    st *= fade[:, None]
    st *= 0.7 / np.max(np.abs(st))
    raw = out_dir / f".{name}.wav"
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    out = out_dir / f"{name}.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-c:a", "aac", "-b:a", "160k", str(out)], check=True)
    raw.unlink()
    (out_dir / f"{name}.m4a.txt").write_text(
        "Composed by tools/make_music.py for Orukural Orukadhai: synthesised from scratch, no samples. "
        "Owned by the channel; no licence or attribution needed.\n", "utf-8")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seconds", type=float, default=60)
    p.add_argument("--out", default=str(ROOT / "assets" / "music"))
    a = p.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in TRACKS.items():
        print(make(name, spec, a.seconds, out_dir))


if __name__ == "__main__":
    main()
