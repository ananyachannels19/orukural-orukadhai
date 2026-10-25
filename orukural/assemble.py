"""Phase 2: cut the shots to the real narration timing and mix narration + music.

Timing: each script segment gets max(its planned length, the real voice length + a short
gap). Shot boundaries are then moved with the segments they sit in (piecewise-linear map
from planned to real time), so pictures stay in sync with the words.

Output: render/<id>_draft.mp4 (9:16, 1080x1920) and render/timeline.json, which the
subtitle and branding step (phase 3) reads.
"""

from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from pathlib import Path

from . import media
from .config import Settings
from .schema import EpisodeScript, Shot

MUSIC_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def real_timeline(s: Settings, script: EpisodeScript, voice: dict) -> tuple[list[dict], list[tuple[float, float]]]:
    gap = s["voice"]["gap_seconds"]
    t, segs, anchors = 0.0, [], [(0.0, 0.0)]
    for seg, v in zip(script.segments, voice["segments"]):
        planned = seg.end_s - seg.start_s
        slot = max(planned, v["seconds"] + gap)
        segs.append({"n": v["n"], "beat": seg.beat, "speaker": seg.speaker, "file": v["file"],
                     "start": round(t, 3), "end": round(t + slot, 3), "voice_seconds": v["seconds"]})
        t += slot
        anchors.append((seg.end_s, t))
    return segs, anchors


def remap(x: float, anchors: list[tuple[float, float]]) -> float:
    xs = [a for a, _ in anchors]
    i = min(max(bisect_right(xs, x) - 1, 0), len(anchors) - 2)
    (x0, y0), (x1, y1) = anchors[i], anchors[i + 1]
    return y0 if x1 == x0 else y0 + (x - x0) * (y1 - y0) / (x1 - x0)


def _encode(s: Settings) -> list[str]:
    return ["-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(s["assembly"]["crf"]),
            "-pix_fmt", "yuv420p", "-r", str(s["assembly"]["fps"])]


def _still_piece(s: Settings, image: Path, seconds: float, punch: float, out: Path) -> None:
    """A held still: no pan, no zoom."""
    vf = f"{media.fill_frame(punch)},fps={s['assembly']['fps']}"
    media.run(["-loop", "1", "-i", str(image), "-t", f"{seconds:.3f}", "-vf", vf, *_encode(s), str(out)])


def _clip_piece(s: Settings, clip: Path, offset: float, seconds: float, punch: float, out: Path) -> None:
    have = media.duration(clip) - offset
    pad = max(0.0, seconds - have) + 0.1
    vf = f"{media.fill_frame(punch)},tpad=stop_mode=clone:stop_duration={pad:.3f},fps={s['assembly']['fps']}"
    media.run(["-ss", f"{max(0.0, offset):.3f}", "-i", str(clip), "-t", f"{seconds:.3f}", "-vf", vf, *_encode(s), str(out)])


def _pieces_for(s: Settings, shot: Shot, start: float, end: float) -> list[tuple[float, float]]:
    """(offset into source, length, punch) cuts for one shot."""
    d = end - start
    punch = s["assembly"]["punch_in"]
    if punch > 1.0 and shot.beat == "story" and d > s["assembly"]["split_story_shots_over"]:
        half = d / 2
        return [(0.0, half, 1.0), (half, d - half, punch)]
    return [(0.0, d, 1.0)]


def pick_music(s: Settings, episode_id: str) -> Path | None:
    mdir = s.root / s["music"]["dir"]
    tracks = sorted(p for p in mdir.glob("*") if p.suffix.lower() in MUSIC_EXT) if mdir.exists() else []
    if not tracks:
        return None
    idx = int(hashlib.sha256(episode_id.encode()).hexdigest(), 16) % len(tracks)
    return tracks[idx]


def _mix_audio(s: Settings, ep_dir: Path, segs: list[dict], total: float, music: Path | None, out: Path) -> None:
    vdir = ep_dir / "voice"
    args, labels, filters = [], [], []
    for i, seg in enumerate(segs):
        args += ["-i", str(vdir / seg["file"])]
        ms = int(seg["start"] * 1000)
        filters.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]")
        labels.append(f"[v{i}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad=whole_dur={total:.3f}[narr]")
    if music:
        m = len(segs)
        args += ["-stream_loop", "-1", "-i", str(music)]
        vol = s["music"]["volume_db"]
        filters.append(f"[{m}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol}dB,"
                       f"afade=t=in:d=0.5,atrim=0:{total:.3f}[bed]")
        if s["music"]["duck"]:
            filters.append("[narr]asplit=2[narr1][key]")
            filters.append("[bed][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[ducked]")
            filters.append("[narr1][ducked]amix=inputs=2:normalize=0[mix]")
        else:
            filters.append("[narr][bed]amix=inputs=2:normalize=0[mix]")
    else:
        filters.append("[narr]anull[mix]")
    filters.append(f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{total:.3f}[out]")
    media.run([*args, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "192k",
               "-ar", "48000", str(out)])


def assemble(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str) -> dict:
    media.require_ffmpeg()
    voice = json.loads((ep_dir / "voice" / "voice.json").read_text("utf-8"))
    visuals = json.loads((ep_dir / "visuals.json").read_text("utf-8"))
    by_n = {v["n"]: v for v in visuals["shots"]}
    missing = [sh.n for sh in script.shots if sh.n not in by_n]
    if missing:
        raise SystemExit(f"no images for shots {missing}; run `studio.py visuals {episode_id}` first")

    waiting = [n for n in visuals.get("animated", []) if not by_n[n]["clip"]]
    if waiting and s["assembly"]["missing_clip"] == "wait":
        raise SystemExit(f"{episode_id}: waiting for clips for shots {waiting}. Make them in Flow when the daily "
                         f"credits reset (`studio.py flow-sheet {episode_id}`), then run visuals and assemble again.")

    segs, anchors = real_timeline(s, script, voice)
    total = segs[-1]["end"]
    rdir = ep_dir / "render"
    pdir = rdir / "pieces"
    pdir.mkdir(parents=True, exist_ok=True)

    shot_rows, pieces = [], []
    for k, sh in enumerate(script.shots):
        start = remap(sh.start_s, anchors)
        end = total if k == len(script.shots) - 1 else remap(sh.end_s, anchors)
        v = by_n[sh.n]
        for j, (off, length, punch) in enumerate(_pieces_for(s, sh, start, end)):
            out = pdir / f"shot{sh.n:02d}_{j}.mp4"
            if v["clip"]:
                _clip_piece(s, ep_dir / "clips" / v["clip"], off, length, punch, out)
            else:
                _still_piece(s, ep_dir / "images" / v["image"], length, punch=punch, out=out)
            pieces.append(out)
        shot_rows.append({"n": sh.n, "beat": sh.beat, "start": round(start, 3), "end": round(end, 3),
                          "source": "clip" if v["clip"] else "still", "cuts": j + 1})

    concat = pdir / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in pieces), "utf-8")
    video_only = rdir / "video_only.mp4"
    media.run(["-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(video_only)])

    music = pick_music(s, episode_id)
    audio = rdir / "audio.m4a"
    _mix_audio(s, ep_dir, segs, total, music, audio)

    final = rdir / f"{episode_id}_draft.mp4"
    media.run(["-i", str(video_only), "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
               "-c:a", "copy", "-t", f"{total:.3f}", "-movflags", "+faststart", str(final)])

    lo, hi = s["episode"]["target_seconds"]
    timeline = {
        "episode_id": episode_id, "dry_run": voice.get("dry_run") or visuals.get("dry_run"),
        "total_seconds": round(total, 3), "within_target": lo <= total <= hi + 1,
        "music": music.name if music else None, "segments": segs, "shots": shot_rows,
        "output": final.name,
    }
    (rdir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), "utf-8")
    return timeline
