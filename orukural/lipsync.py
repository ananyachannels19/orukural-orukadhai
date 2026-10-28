"""Exact lip sync: Flow speaks the line, our voice takes its place.

A clip made silent and dubbed afterwards only roughly matches: the model guesses when the mouth moves.
So for every line spoken by a character on screen and held within one shot, the clip prompt gives
Flow the exact Tamil words and asks the character to say them. Flow then animates lips, jaw, breath
and gesture to its own speech, and its soundtrack tells us exactly when that speech starts and stops.
At assembly our narration voice (the consistent character voice) is trimmed to its first and last
word, stretched to the length of Flow's speech, and laid at the moment Flow's speech starts; the
picture is offset so that moment lands where the line sits in the timeline. Flow's own voice is never
heard (the talking shots' clip sound is muted).

The fit is phrase by phrase: our line is split at its own pauses, Flow's speech at its pauses, and
each of our phrases is stretched onto its own stretch of Flow's speech, so the mouth closes when our
voice pauses (a whole-line stretch only gets the first and last word right).

Speech is found from the clip's sound by energy in the voice band. When that guess is wrong (a loud
bark, music), `episodes/<id>/lipsync.json` can pin it: {"6": [[0.6, 2.9], [3.4, 5.5]]} gives the
speech spans of shot 6 in clip seconds, one per spoken line in order; a line given as a list of
phrases, {"5": [[[1.47, 1.94], [3.53, 5.06]]]}, pins its phrases too. Pinned seconds are those of
the clip as Flow made it, before any cut from edit.py.

Flow's own voice can be kept instead where it says the right words in a voice that suits the
character: {"flow_voice": [5, 9]} in the same file. Its lines then play straight from the clip's
sound (perfect sync by construction); the narrator and lines it gets wrong stay on our voice.

Per character, the cast's `voice_source` (tts by default, or flow) does the same for every shot they
speak in; the per-episode review sets it in lipsync.json, {"voice_source": {"vignesh": "flow"}}, after
listening to `studio.py voice-ab N` (Flow's voice, then ours, for each line). Choose flow only when
the Tamil is clear and the character sounds the same in all their clips."""
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


def _parts(gaps: list[tuple[float, float]], a: float, b: float, min_len: float = 0.1) -> list[tuple[float, float]]:
    """The sounding stretches between a and b, given the quiet stretches of the whole file."""
    out, t = [], a
    for g0, g1 in sorted(gaps) + [(b, b)]:
        g0, g1 = max(a, min(b, g0)), max(a, min(b, g1))
        if g0 - t >= min_len:
            out.append((t, g0))
        t = max(t, g1)
    return out


def merge_parts(parts: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    """Join the closest neighbours until `count` parts are left."""
    parts = list(parts)
    while len(parts) > max(1, count):
        k = min(range(len(parts) - 1), key=lambda j: parts[j + 1][0] - parts[j][1])
        parts[k:k + 2] = [(parts[k][0], parts[k + 1][1])]
    return parts


def _phrases(path: Path, v0: float, v1: float) -> list[tuple[float, float]]:
    """Our voice split at its own pauses (a comma or a full stop in the line)."""
    return _parts(media.pauses(path, min_seconds=0.12, noise_db=-40), v0, v1) or [(v0, v1)]


def _flow_parts(clip: Path, a: float, b: float) -> list[tuple[float, float]]:
    """Flow's speech between a and b split at its pauses (voice band only, as in speech_spans)."""
    quiet = media.pauses(clip, min_seconds=0.12, noise_db=-32, af="highpass=f=180,lowpass=f=3800")
    return _parts(quiet, a, b) or [(a, b)]


def _place_phrases(src: Path, phrases: list[tuple[float, float]], targets: list[tuple[float, float]], out: Path
                   ) -> list[float]:
    """Stretch each phrase of our voice onto its own stretch of Flow's speech, so our pauses fall where Flow's
    mouth closes. Writes one file starting at targets[0][0]; returns the tempo used per phrase."""
    args, chain, labels, tempos, t_free = [], [], [], [], 0.0
    for k, ((p0, p1), (q0, q1)) in enumerate(zip(phrases, targets)):
        tempo = min(STRETCH[1], max(STRETCH[0], (p1 - p0) / (q1 - q0)))
        at = max(q0 - targets[0][0], t_free)  # a phrase that could not be squeezed enough pushes the next one on
        t_free = at + (p1 - p0) / tempo + 0.04
        args += ["-ss", f"{p0:.3f}", "-t", f"{p1 - p0:.3f}", "-i", str(src)]
        ms = int(round(at * 1000))
        chain.append(f"[{k}:a]aresample=44100,aformat=channel_layouts=stereo,atempo={tempo:.4f},adelay={ms}|{ms}[p{k}]")
        labels.append(f"[p{k}]")
        tempos.append(tempo)
    chain.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0[out]")
    media.run([*args, "-filter_complex", ";".join(chain), "-map", "[out]", "-ar", "44100", str(out)])
    return tempos


def _span(v) -> list[tuple[float, float]]:
    """A pinned line: [a, b] (its whole speech) or [[a, b], [c, d], ...] (its phrases)."""
    return [tuple(v)] if isinstance(v[0], (int, float)) else [tuple(x) for x in v]


def load_pins(ep_dir: Path) -> dict:
    f = ep_dir / "lipsync.json"
    return json.loads(f.read_text("utf-8")) if f.exists() else {}


def voice_sources(script: EpisodeScript, pins: dict) -> dict[str, str]:
    """Per character: "flow" (Flow's own voice) or "tts" (ours, fitted). The episode review overrides the cast."""
    out = {c.id: c.voice_source for c in script.cast}
    out.update(pins.get("voice_source") or {})
    return out


def fit(s: Settings, ep_dir: Path, script: EpisodeScript, segs: list[dict], shots: list[tuple[Shot, float, float]],
        clips: dict[int, Path], to_clip: dict | None = None) -> tuple[list[dict], dict[int, float], list[str]]:
    """Move each on-screen line onto Flow's speech. shots: (shot, real start, real end).
    to_clip: per shot, a function from the original clip's seconds to the (edited) clip's, for pinned spans.
    Returns the updated segments, a picture offset (clip seconds) per shot, and notes for the log."""
    raw = load_pins(ep_dir)
    flow_voice = {int(n) for n in raw.pop("flow_voice", [])}
    sources = voice_sources(script, raw)
    raw.pop("voice_source", None)
    pinned = {int(k): [_span(x) for x in v] for k, v in raw.items()}
    out_dir = ep_dir / "render" / "fit"
    segs = [dict(g) for g in segs]
    offsets, notes = {}, []
    for shot, start, end in shots:
        lines = spoken_lines(script, shot)
        clip = clips.get(shot.n)
        if not lines or not clip:
            continue
        move = (to_clip or {}).get(shot.n) or (lambda t: t)
        given = [[(move(x), move(y)) for x, y in line] for line in pinned.get(shot.n, [])]
        spans = [(line[0][0], line[-1][1]) for line in given] or speech_spans(clip, len(lines))
        if len(spans) != len(lines):
            notes.append(f"shot {shot.n}: no clear speech in the clip; voice left where it was")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        first = segs[lines[0]]
        # show the clip from the point where its speech lands on our line's slot
        offset = max(0.0, spans[0][0] - (first["start"] - start))
        offsets[shot.n] = offset
        for j, (i, (a, b)) in enumerate(zip(lines, spans)):
            g = segs[i]
            fitted = out_dir / f"seg{i + 1:02d}.wav"
            if shot.n in flow_voice or sources.get(script.segments[i].speaker) == "flow":  # Flow's own voice, cut from the clip
                lead = max(0.0, min(0.05, a, start + a - offset))  # never before the clip or the film starts
                media.run(["-ss", f"{a - lead:.3f}", "-t", f"{b - a + lead + 0.05:.3f}", "-i", str(clip), "-vn",
                           "-ar", "44100", "-ac", "2", str(fitted)])
                g.update(start=round(start + a - lead - offset, 3), voice_seconds=round(media.duration(fitted), 3),
                         file=str(fitted), path=str(fitted),
                         lipsync={"shot": shot.n, "flow_speech": [round(a, 2), round(b, 2)], "voice": "flow"})
                notes.append(f"shot {shot.n}: line {i + 1} uses Flow's own voice ({a:.2f}-{b:.2f} s)")
                continue
            src = ep_dir / "voice" / g["file"]
            v0, v1 = _voice_bounds(src)
            # phrase by phrase: as many of our phrases as Flow has stretches of speech (the closest ones joined)
            ours = _phrases(src, v0, v1)
            flows = given[j] if given and len(given[j]) > 1 else _flow_parts(clip, a, b)
            k = min(len(ours), len(flows))
            ours, flows = merge_parts(ours, k), merge_parts(flows, k)
            for (p0, p1), (q0, q1) in zip(ours, flows):
                speed = (p1 - p0) / (q1 - q0)
                if not STRETCH[0] <= speed <= STRETCH[1]:
                    notes.append(f"shot {shot.n}: line {i + 1} phrase at {q0:.2f} s needed {speed:.2f}x to fit "
                                 f"Flow's speech; capped")
            tempos = _place_phrases(src, ours, flows, fitted)
            g["start"] = round(start + flows[0][0] - offset, 3)
            g["voice_seconds"] = round(media.duration(fitted), 3)
            g["file"] = str(fitted)
            g["path"] = str(fitted)
            g["lipsync"] = {"shot": shot.n, "flow_speech": [[round(q0, 2), round(q1, 2)] for q0, q1 in flows],
                            "tempo": [round(t, 3) for t in tempos]}
            notes.append(f"shot {shot.n}: line {i + 1} on Flow's speech "
                         + ", ".join(f"{q0:.2f}-{q1:.2f}" for q0, q1 in flows) + " s, voice at "
                         + ", ".join(f"{t:.2f}x" for t in tempos))
    for prev, nxt in zip(segs, segs[1:]):
        if prev["start"] + prev["voice_seconds"] > nxt["start"] + 0.05:
            notes.append(f"line {nxt['n']} starts before line {prev['n']} ends ({nxt['start']:.2f} s): check that cut")
    return segs, offsets, notes


def ab_preview(s: Settings, ep_dir: Path, script: EpisodeScript, clips: dict[int, Path], out_dir: Path) -> list[Path]:
    """Per character: each of their on-screen lines as Flow said it (A), a beat of silence, then ours (B),
    so the review can pick voice_source by ear. Returns one .m4a per character."""
    pins = {int(k): [_span(x) for x in v] for k, v in load_pins(ep_dir).items() if k.isdigit()}
    out_dir.mkdir(parents=True, exist_ok=True)
    parts: dict[str, list[Path]] = {}
    tmp = out_dir / "ab_parts"
    tmp.mkdir(exist_ok=True)
    gap = tmp / "gap.wav"
    media.run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "0.6", str(gap)])
    for shot in script.shots:
        clip, lines = clips.get(shot.n), spoken_lines(script, shot)
        if not clip or not lines:
            continue
        spans = [(x[0][0], x[-1][1]) for x in pins.get(shot.n, [])] or speech_spans(clip, len(lines))
        if len(spans) != len(lines):
            continue
        for i, (a, b) in zip(lines, spans):
            seg = script.segments[i]
            flow = tmp / f"seg{i + 1:02d}_flow.wav"
            ours = tmp / f"seg{i + 1:02d}_tts.wav"
            media.run(["-ss", f"{a:.3f}", "-t", f"{b - a + 0.1:.3f}", "-i", str(clip), "-vn", "-ar", "44100", "-ac", "2",
                       str(flow)])
            src = next(ep_dir.glob(f"voice/seg{i + 1:02d}_*.mp3"), None)
            if not src:
                continue
            media.run(["-i", str(src), "-ar", "44100", "-ac", "2", str(ours)])
            parts.setdefault(seg.speaker, []).extend([flow, gap, ours, gap, gap])
    made = []
    for who, files in parts.items():
        out = out_dir / f"voice_ab_{who}.m4a"
        lst = tmp / f"{who}.txt"
        lst.write_text("".join(f"file '{f.resolve()}'\n" for f in files), "utf-8")
        media.run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "aac", "-b:a", "160k", str(out)])
        made.append(out)
    return made
