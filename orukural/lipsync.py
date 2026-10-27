"""Exact lip sync: Flow speaks the line, our voice takes its place.

A clip made silent and dubbed afterwards only roughly matches: the model guesses when the mouth moves.
So for every line spoken by a character on screen and held within one shot, the clip prompt gives
Flow the exact Tamil words and asks the character to say them. Flow then animates lips, jaw, breath
and gesture to its own speech, and its soundtrack tells us exactly when that speech starts and stops.
At assembly our narration voice (the consistent character voice) is trimmed to its first and last
word, stretched to the length of Flow's speech, and laid at the moment Flow's speech starts; the
picture is offset so that moment lands where the line sits in the timeline. Flow's own voice is never
heard (the talking shots' clip sound is muted).

Speech is found from the clip's sound by energy in the voice band. When that guess is wrong (a loud
bark, music), `episodes/<id>/lipsync.json` can pin it: {"6": [[0.6, 2.9], [3.4, 5.5]]} gives the
speech spans of shot 6 in clip seconds, one per spoken line in order.

Flow's own voice can be kept instead where it says the right words in a voice that suits the
character: {"flow_voice": [5, 9]} in the same file. Its lines then play straight from the clip's
sound (perfect sync by construction); the narrator and lines it gets wrong stay on our voice."""
from __future__ import annotations

import json
from pathlib import Path

from . import media
from .config import Settings
from .schema import EpisodeScript, Shot

STRETCH = (0.8, 1.25)  # beyond this the voice sounds wrong: fit as far as allowed and warn


def spoken_lines(script: EpisodeScript, shot: Shot) -> list[int]:
    """Indexes of the segments a character on screen speaks wholly inside this shot (Flow can say these)."""
    out = []
    for i, seg in enumerate(script.segments):
        inside = min(seg.end_s, shot.end_s) - max(seg.start_s, shot.start_s)
        if seg.speaker in shot.characters and inside >= 0.9 * (seg.end_s - seg.start_s):
            out.append(i)
    return out


def needed_seconds(script: EpisodeScript, shot: Shot) -> float:
    """Clip length that leaves room for every spoken line plus a breath either side."""
    lines = spoken_lines(script, shot)
    return sum(script.segments[i].end_s - script.segments[i].start_s for i in lines) + 1.0 if lines else 0.0


def speech_spans(clip: Path, count: int) -> list[tuple[float, float]]:
    """`count` (start, end) spans of speech in a clip's sound, split at its longest silences."""
    if count < 1 or not media.has_audio(clip):
        return []
    dur = media.duration(clip)
    # voice band only, so footsteps and rumble don't read as talk
    quiet = media.pauses(clip, min_seconds=0.12, noise_db=-32, af="highpass=f=180,lowpass=f=3800")
    sound, t = [], 0.0
    for a, b in quiet + [(dur, dur)]:
        if a - t >= 0.15:
            sound.append((t, a))
        t = b
    if len(sound) < count:
        return []
    gaps = sorted(range(len(sound) - 1), key=lambda k: sound[k + 1][0] - sound[k][1], reverse=True)[: count - 1]
    spans, start = [], 0
    for k in sorted(gaps) + [len(sound) - 1]:
        spans.append((sound[start][0], sound[k][1]))
        start = k + 1
    return spans


def _voice_bounds(path: Path) -> tuple[float, float]:
    """First and last sound in one of our voice files."""
    dur = media.duration(path)
    gaps = media.pauses(path, min_seconds=0.08, noise_db=-40)
    onset = next((b for a, b in gaps if a <= 0.03), 0.0)
    stop = next((a for a, b in gaps if b >= dur - 0.03 and a > onset), dur)
    return onset, stop


def fit(s: Settings, ep_dir: Path, script: EpisodeScript, segs: list[dict], shots: list[tuple[Shot, float, float]],
        clips: dict[int, Path]) -> tuple[list[dict], dict[int, float], list[str]]:
    """Move each on-screen line onto Flow's speech. shots: (shot, real start, real end).
    Returns the updated segments, a picture offset (clip seconds) per shot, and notes for the log."""
    pinned, flow_voice = {}, set()
    pin_file = ep_dir / "lipsync.json"
    if pin_file.exists():
        raw = json.loads(pin_file.read_text("utf-8"))
        flow_voice = {int(n) for n in raw.pop("flow_voice", [])}
        pinned = {int(k): [tuple(x) for x in v] for k, v in raw.items()}
    out_dir = ep_dir / "render" / "fit"
    segs = [dict(g) for g in segs]
    offsets, notes = {}, []
    for shot, start, end in shots:
        lines = spoken_lines(script, shot)
        clip = clips.get(shot.n)
        if not lines or not clip:
            continue
        spans = pinned.get(shot.n) or speech_spans(clip, len(lines))
        if len(spans) != len(lines):
            notes.append(f"shot {shot.n}: no clear speech in the clip; voice left where it was")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        first = segs[lines[0]]
        # show the clip from the point where its speech lands on our line's slot
        offset = max(0.0, spans[0][0] - (first["start"] - start))
        offsets[shot.n] = offset
        for i, (a, b) in zip(lines, spans):
            g = segs[i]
            fitted = out_dir / f"seg{i + 1:02d}.wav"
            if shot.n in flow_voice:  # Flow's own voice, cut straight from the clip
                media.run(["-ss", f"{max(0.0, a - 0.05):.3f}", "-t", f"{b - a + 0.1:.3f}", "-i", str(clip), "-vn",
                           "-ar", "44100", "-ac", "2", str(fitted)])
                g.update(start=round(start + a - 0.05 - offset, 3), voice_seconds=round(media.duration(fitted), 3),
                         file=str(fitted), path=str(fitted),
                         lipsync={"shot": shot.n, "flow_speech": [round(a, 2), round(b, 2)], "voice": "flow"})
                notes.append(f"shot {shot.n}: line {i + 1} uses Flow's own voice ({a:.2f}-{b:.2f} s)")
                continue
            src = ep_dir / "voice" / g["file"]
            v0, v1 = _voice_bounds(src)
            speed = (v1 - v0) / (b - a)
            tempo = min(STRETCH[1], max(STRETCH[0], speed))
            if tempo != speed:
                notes.append(f"shot {shot.n}: line {i + 1} needed {speed:.2f}x to fit Flow's speech; capped at {tempo:.2f}x")
            media.run(["-ss", f"{v0:.3f}", "-t", f"{v1 - v0:.3f}", "-i", str(src), "-af",
                       f"atempo={tempo:.4f}", "-ar", "44100", str(fitted)])
            g["start"] = round(start + a - offset, 3)
            g["voice_seconds"] = round(media.duration(fitted), 3)
            g["file"] = str(fitted)
            g["path"] = str(fitted)
            g["lipsync"] = {"shot": shot.n, "flow_speech": [round(a, 2), round(b, 2)], "tempo": round(tempo, 3)}
            notes.append(f"shot {shot.n}: line {i + 1} on Flow's speech {a:.2f}-{b:.2f} s, voice at {tempo:.2f}x")
    for prev, nxt in zip(segs, segs[1:]):
        if prev["start"] + prev["voice_seconds"] > nxt["start"] + 0.05:
            notes.append(f"line {nxt['n']} starts before line {prev['n']} ends ({nxt['start']:.2f} s): check that cut")
    return segs, offsets, notes
