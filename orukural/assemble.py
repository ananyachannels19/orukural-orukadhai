"""Phase 2: cut the shots to the real narration timing and mix narration + music.

Timing: each script segment gets max(its planned length, the real voice length + a short
gap). Shot boundaries are then moved with the segments they sit in (piecewise-linear map
from planned to real time), so pictures stay in sync with the words.

Output: render/<id>_draft.mp4 (9:16, 1080x1920) and render/timeline.json, which the
subtitle and branding step (phase 3) reads.
"""

from __future__ import annotations

import copy
import hashlib
import json
from bisect import bisect_right
from pathlib import Path

from . import captions, continuity, edit, lipsync, live, media, signature
from .config import Settings
from .kurals import KuralStore
from .schema import EpisodeScript, Shot

MUSIC_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def real_timeline(s: Settings, script: EpisodeScript, voice: dict) -> tuple[list[dict], list[tuple[float, float]]]:
    gap = s["voice"]["gap_seconds"]
    t, segs, anchors = 0.0, [], [(0.0, 0.0)]
    prev_end = None
    for seg, v in zip(script.segments, voice["segments"]):
        # a deliberate silent beat in the script (a silent shot, a pause before a line) is kept as real time:
        # without it the beat is squeezed away and the next line plays over the wrong picture
        if prev_end is not None and seg.start_s - prev_end > 0.3:
            t += seg.start_s - prev_end
            anchors.append((seg.start_s, t))
        prev_end = seg.end_s
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
    return ["-an", "-c:v", "libx264", "-preset", s["assembly"].get("preset", "medium"), "-crf", str(s["assembly"]["crf"]),
            "-pix_fmt", "yuv420p", "-r", str(s["assembly"]["fps"])]


def _still_piece(s: Settings, image: Path, seconds: float, punch: float, out: Path) -> None:
    """A held still: no pan, no zoom."""
    vf = f"{media.fill_frame(punch)},fps={s['assembly']['fps']}"
    media.run(["-loop", "1", "-i", str(image), "-t", f"{seconds:.3f}", "-vf", vf, *_encode(s), str(out)])


def _clip_piece(s: Settings, clip: Path, offset: float, seconds: float, punch: float, out: Path) -> None:
    have = media.video_duration(clip) - offset
    # a clip a little short of its shot (Flow's 1080p upscale drops the last frame or two) is slowed to fit,
    # by no more than 0.85x, rather than freezing on its last frame; the tpad only covers rounding
    slow = seconds / have if have < seconds and have >= 0.85 * seconds else 1.0
    pad = max(0.0, seconds - have * slow) + 0.1
    stretch = f"setpts={slow:.5f}*PTS," if slow > 1.0 else ""
    vf = (f"{stretch}{media.fill_frame(punch)},tpad=stop_mode=clone:stop_duration={pad:.3f},"
          f"fps={s['assembly']['fps']}")
    media.run(["-ss", f"{max(0.0, offset):.3f}", "-i", str(clip), "-t", f"{seconds:.3f}", "-vf", vf, *_encode(s), str(out)])


def _pieces_for(s: Settings, shot: Shot, start: float, end: float) -> list[tuple[float, float]]:
    """(offset into source, length, punch) cuts for one shot."""
    d = end - start
    punch = s["assembly"]["punch_in"]
    if punch > 1.0 and shot.beat == "story" and d > s["assembly"]["split_story_shots_over"]:
        half = d / 2
        return [(0.0, half, 1.0), (half, d - half, punch)]
    return [(0.0, d, 1.0)]


def _shot_at(rows: list[dict], t: float) -> int | str:
    return next((r["n"] for r in rows if r["start"] <= t + 0.05 < r["end"]), "?")


def pick_music(s: Settings, episode_id: str) -> Path | None:
    mdir = s.root / s["music"]["dir"]
    tracks = sorted(p for p in mdir.glob("*") if p.suffix.lower() in MUSIC_EXT) if mdir.exists() else []
    if not tracks:
        return None
    idx = int(hashlib.sha256(episode_id.encode()).hexdigest(), 16) % len(tracks)
    return tracks[idx]


def _speech(clip: Path) -> list[tuple[float, float]]:
    """Where someone speaks in a clip's own sound (voice band), with a little room either side."""
    return [(max(0.0, a - 0.1), b + 0.15) for a, b in lipsync._flow_parts(clip, 0.0, media.duration(clip))
            if b - a >= 0.15]


def _fx_piece(clip: Path | None, offset: float, seconds: float, out: Path,
              mute: list[tuple[float, float]] = ()) -> None:
    """The clip's own sound for one cut (footsteps, the puppy, the street), or silence: always exactly as long
    as the picture so the concatenated track stays in sync. `mute`: clip seconds to silence (speech)."""
    if clip and media.has_audio(clip):
        off = max(0.0, offset)
        hush = "".join(f"volume=0:enable='between(t,{a - off:.3f},{b - off:.3f})'," for a, b in mute
                       if b > off and a < off + seconds)
        media.run(["-ss", f"{off:.3f}", "-i", str(clip), "-vn", "-af",
                   f"{hush}aresample=44100,aformat=channel_layouts=stereo,apad,atrim=0:{seconds:.3f}",
                   "-c:a", "pcm_s16le", str(out)])
    else:
        media.run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{seconds:.3f}", "-c:a", "pcm_s16le", str(out)])


def _mix_audio(s: Settings, ep_dir: Path, segs: list[dict], total: float, music: Path | None, out: Path,
               fx: Path | None = None, extra: list[tuple[Path, float, float]] | None = None) -> None:
    """`extra`: sound effects and ambience (file, film second, gain dB), mixed into the scene-sound layer so
    they dip under the voices."""
    vdir = ep_dir / "voice"
    args, labels, filters = [], [], []
    if extra:  # one scene-sound track: the clips' own sound (if any) plus the effects
        fx = _effects_track(s, ep_dir, total, fx, extra)
    for i, seg in enumerate(segs):
        args += ["-i", str(vdir / seg["file"])]
        ms = int(seg["start"] * 1000)
        filters.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{i}]")
        labels.append(f"[v{i}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad=whole_dur={total:.3f}[narr0]")
    if fx:
        # the scene's own sound under the voice, dipped while someone speaks
        nat = s["assembly"].get("natural_sound") or {}
        args += ["-i", str(fx)]
        filters.append(f"[narr0]asplit=2[narr1][fxkey]")
        filters.append(f"[{len(segs)}:a]volume={nat.get('volume_db', -6)}dB,apad=whole_dur={total:.3f}[fx0]")
        filters.append("[fx0][fxkey]sidechaincompress=threshold=0.02:ratio=4:attack=15:release=350[fx1]")
        filters.append("[narr1][fx1]amix=inputs=2:normalize=0[narr]")
    else:
        filters.append("[narr0]anull[narr]")
    if music:
        m = len(segs) + (1 if fx else 0)
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
    loud = s["assembly"].get("loudness") or {}
    filters.append(f"[mix]loudnorm=I={loud.get('lufs', -14)}:TP={loud.get('true_peak', -1) - 0.5}:LRA=11,"
                   f"atrim=0:{total:.3f}[out]")
    media.run([*args, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", f"{s['assembly'].get('audio_kbps', 192)}k",
               "-ar", "48000", str(out)])


def _effects_track(s: Settings, ep_dir: Path, total: float, fx: Path | None,
                   extra: list[tuple[Path, float, float]]) -> Path:
    """The scene-sound layer with the effects laid in at their film seconds (at the natural-sound level, the
    effects' own gain on top)."""
    nat_db = (s["assembly"].get("natural_sound") or {}).get("volume_db", -6)
    args, filters, labels = [], [], []
    k = 0
    if fx:
        args += ["-i", str(fx)]
        filters.append(f"[0:a]aresample=44100,aformat=channel_layouts=stereo[e0]")
        labels.append("[e0]")
        k = 1
    for j, (path, at, gain) in enumerate(extra):
        args += ["-i", str(path)]
        ms = max(0, int(at * 1000))
        # natural_sound's volume is applied to this whole layer later; undo it here so `gain` is the effect's level
        filters.append(f"[{k + j}:a]aresample=44100,aformat=channel_layouts=stereo,volume={gain - nat_db}dB,"
                       f"adelay={ms}|{ms}[e{k + j}]")
        labels.append(f"[e{k + j}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad=whole_dur={total:.3f},"
                   f"atrim=0:{total:.3f}[out]")
    out = ep_dir / "render" / "effects.wav"
    media.run([*args, "-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "pcm_s16le", str(out)])
    return out


def _effect_list(ep_dir: Path, over: dict, shot_rows: list[dict], total: float) -> list[tuple[Path, float, float]]:
    """edit.json "sfx" and "ambience" as (file, film second, gain dB)."""
    starts = {r["n"]: r["start"] for r in shot_rows}
    out = []
    if amb := over.get("ambience"):
        out.append((ep_dir / amb["file"], 0.0, float(amb.get("gain_db", -26))))
    for e in over.get("sfx") or []:
        if e.get("shot") not in starts:
            continue
        out.append((ep_dir / e["file"], starts[e["shot"]] + float(e.get("at", 0.0)), float(e.get("gain_db", -12))))
    return [(p, a, g) for p, a, g in out if p.exists() and a < total]


def master(s: Settings) -> Settings:
    """The same settings with assembly.final (crf, preset, audio) applied: the slower upload master."""
    m = copy.deepcopy(s)
    m.raw["assembly"].update(m.raw["assembly"].get("final") or {})
    m.raw["assembly"]["output_name"] = "final"
    return m


def assemble(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str, final: bool = False) -> dict:
    if final:
        s = master(s)
    if s.dry_run:
        return _assemble(s, ep_dir, script, episode_id)
    live.emit(s, episode_id, "render", "start")
    try:
        t = _assemble(s, ep_dir, script, episode_id)
    except SystemExit as e:
        live.emit(s, episode_id, "render", "blocked", str(e)[:300])
        raise
    except Exception as e:
        live.emit(s, episode_id, "render", "fail", str(e)[:300])
        raise
    live.emit(s, episode_id, "render", "done", t["output"], seconds=t["total_seconds"])
    return t


def _assemble(s: Settings, ep_dir: Path, script: EpisodeScript, episode_id: str) -> dict:
    media.require_ffmpeg()
    voice = json.loads((ep_dir / "voice" / "voice.json").read_text("utf-8"))
    from .voice import too_long
    if bad := ([] if voice.get("dry_run") else too_long(s, script, voice)):
        raise SystemExit(f"{episode_id}: voice lines too long, not rendering: " + "; ".join(bad)
                         + ". Listen to them; remake with `studio.py voice` once fixed.")
    visuals = json.loads((ep_dir / "visuals.json").read_text("utf-8"))
    by_n = {v["n"]: v for v in visuals["shots"]}
    missing = [sh.n for sh in script.shots if sh.n not in by_n]
    if missing:
        raise SystemExit(f"no images for shots {missing}; run `studio.py visuals {episode_id}` first")

    waiting = [n for n in visuals.get("animated", []) if not by_n[n]["clip"]]
    if waiting and s["assembly"]["missing_clip"] == "wait":
        raise SystemExit(f"{episode_id}: waiting for clips for shots {waiting}. Make them in Flow when the daily "
                         f"credits reset (`studio.py flow-sheet {episode_id}`), then run visuals and assemble again.")

    if s["continuity"]["require_review"] and not s.dry_run:
        review = continuity.load_review(ep_dir)
        gaps = [f"image {g}" for g in continuity.review_gaps(script, review, "images")]
        gaps += [f"clip {g}" for g in continuity.review_gaps(script, review, "clips",
                                                             [n for n in visuals.get("animated", []) if by_n[n]["clip"]])]
        if gaps:
            raise SystemExit(f"{episode_id}: continuity review not passed: " + "; ".join(gaps)
                             + f". Run `studio.py continuity-sheet {episode_id}` and review.")

    segs, anchors = real_timeline(s, script, voice)
    total = segs[-1]["end"]
    rdir = ep_dir / "render"
    pdir = rdir / "pieces"
    pdir.mkdir(parents=True, exist_ok=True)

    spans = [(sh, remap(sh.start_s, anchors), total if k == len(script.shots) - 1 else remap(sh.end_s, anchors))
             for k, sh in enumerate(script.shots)]
    offsets = {}
    clips = {n: ep_dir / "clips" / v["clip"] for n, v in by_n.items() if v["clip"]}
    kural = KuralStore(s.path("kurals")).by_number.get(script.kural_number)
    clips, moves = edit.prepare(s, ep_dir, script, kural, clips)  # cuts, kural card, sharpening (edit.json)
    if (s.raw.get("lipsync") or {}).get("enabled", True):
        segs, offsets, notes = lipsync.fit(s, ep_dir, script, segs, spans, clips, moves)
        for note in notes:
            print(f"lip sync: {note}")

    nat = s["assembly"].get("natural_sound") or {}
    shot_rows, pieces, fx_pieces = [], [], []
    for sh, start, end in spans:
        v = by_n[sh.n]
        for j, (off, length, punch) in enumerate(_pieces_for(s, sh, start, end)):
            off += offsets.get(sh.n, 0.0) + sh.clip_offset_s  # a second cut starts later in the clip it reuses
            out = pdir / f"shot{sh.n:02d}_{j}.mp4"
            clip = clips.get(sh.n)
            if clip:
                _clip_piece(s, clip, off, length, punch, out)
            else:
                _still_piece(s, ep_dir / "images" / v["image"], length, punch=punch, out=out)
            pieces.append(out)
            if nat.get("enabled", True):
                # Flow invents a voice when a character on screen talks: keep only the narration there
                quiet = nat.get("mute_talking_shots", True) and continuity.someone_talks(s, script, sh)
                fx_pieces.append(pdir / f"shot{sh.n:02d}_{j}.wav")
                # a second cut of a talking take keeps its street sound but not the line Flow said in it
                mute = _speech(clip) if not quiet and clip and sh.clip_from and lipsync.spoken_lines(
                    script, next(x for x in script.shots if x.n == sh.clip_from)) else []
                _fx_piece(None if quiet else clip, off, length, fx_pieces[-1], mute)
        shot_rows.append({"n": sh.n, "beat": sh.beat, "start": round(start, 3), "end": round(end, 3),
                          "source": "clip" if v["clip"] else "still", "cuts": j + 1})

    concat = pdir / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in pieces), "utf-8")
    video_only = rdir / "video_only.mp4"
    media.run(["-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(video_only)])
    # no held frames: a clip that runs out under its shot freezes on its last frame
    limit = s["assembly"].get("max_frozen_seconds", 0.3)
    # (a shot that is still from start to end is a held image on purpose, not a clip running out)
    meant = {n for n, spec in edit.load(ep_dir).items() if spec.get("still")}  # a deliberate held frame
    whole = lambda a, b: any((r["start"] >= a - 0.1 and r["end"] <= b + 0.1) or r["n"] in meant
                             for r in shot_rows if r["start"] < b and a < r["end"])
    if held := [(a, b) for a, b in media.frozen(video_only, limit) if not whole(a, b)]:
        where = ", ".join(f"{a:.2f}-{b:.2f} s (shot {_shot_at(shot_rows, a)})" for a, b in held)
        raise SystemExit(f"{episode_id}: the picture freezes at {where}: a clip is shorter than its shot. "
                         f"Retime the shot, or slow the clip (no more than 0.85x), then render again.")

    fx = None
    if fx_pieces:
        fx = rdir / "natural_sound.wav"
        (pdir / "fx.txt").write_text("".join(f"file '{p.name}'\n" for p in fx_pieces), "utf-8")
        media.run(["-f", "concat", "-safe", "0", "-i", str(pdir / "fx.txt"), "-c", "copy", str(fx)])

    music = pick_music(s, episode_id)
    audio = rdir / "audio.m4a"
    extra = _effect_list(ep_dir, edit.episode_overrides(ep_dir), shot_rows, total)
    _mix_audio(s, ep_dir, segs, total, music, audio, fx, extra)

    # the verse is on screen until the cut out of the last kural shot; the rest of the line gets subtitles
    cut = next((r["end"] for r in reversed(shot_rows) if r["beat"] == "kural"), None)
    for g in segs:
        if g["beat"] == "kural" and cut is not None and g["start"] < cut < g["end"] - 0.3:
            g["kural_until"] = cut

    final = rdir / f"{episode_id}_{s['assembly'].get('output_name', 'draft')}.mp4"
    inputs = ["-i", str(video_only)]
    count = 1  # ffmpeg inputs so far
    cuts = [r["start"] for r in shot_rows[1:]]
    segs = [{**g, "path": str(ep_dir / "voice" / g["file"])} for g in segs]  # subtitles follow the voice's pauses
    if captions.ffmpeg_has_ass():
        ass = captions.write_ass(s, script, segs, total, rdir / "captions.ass", cuts)
        graph = f"[0:v]{captions.filter_arg(s, ass)}[t]"
    else:  # e.g. Homebrew's ffmpeg has no libass: overlay pre-drawn subtitle images instead
        graph, last = "", "0:v"
        for k, (png, a, b, y) in enumerate(captions.render_pngs(s, script, segs, total, rdir / "subs", cuts)):
            inputs += ["-i", str(png)]
            graph += f"[{last}][{count}:v]overlay=0:{y}:enable='gte(t,{a:.3f})*lt(t,{b:.3f})'[s{k}];"
            last, count = f"s{k}", count + 1
        graph += f"[{last}]null[t]"
    cover = s["assembly"].get("watermark_cover") or {}
    badge = s.root / cover["image"] if cover.get("image") else None
    if badge and badge.exists():
        # Flow puts a sparkle watermark bottom-right on every image and clip: cover it with the channel badge.
        inputs += ["-i", str(badge)]
        graph += f";[t][{count}:v]overlay={cover['x']}:{cover['y']}[w]"
        count += 1
    else:
        graph += ";[t]null[w]"
    # the channel signature: the kural reveal while it is said, then the logo ending
    sig = signature.plan(s, kural, segs, total, rdir)
    length = total
    if sig:
        ins, chain, vlab = signature.video_graph(sig, "w", count)
        inputs += ins
        count += ins.count("-i")
        graph += ";" + ";".join(chain) + f";[{vlab}]null[v]"
        length = total + sig["ending_seconds"]
    else:
        graph += ";[w]null[v]"
    inputs += ["-i", str(audio)]
    alab, count = f"{count}:a", count + 1
    acodec = ["-c:a", "copy"]
    if sig:
        ins, chain, alab = signature.audio_graph(sig, alab, count)
        inputs += ins
        graph += ";" + ";".join(chain)
        alab = f"[{alab}]"
        acodec = ["-c:a", "aac", "-b:a", f"{s['assembly'].get('audio_kbps', 192)}k", "-ar", "48000"]
    media.run([*inputs, "-filter_complex", graph, "-map", "[v]", "-map", alab,
               "-c:v", "libx264", "-preset", s["assembly"].get("preset", "medium"), "-crf", str(s["assembly"]["crf"]),
               "-pix_fmt", "yuv420p", *acodec,
               "-t", f"{length:.3f}", "-movflags", "+faststart", str(final)])
    # the flute ending is mixed in after the first loudnorm: measure the finished film and correct it
    loud = s["assembly"].get("loudness") or {}
    measured = media.normalize_loudness(final, loud.get("lufs", -14), loud.get("true_peak", -1),
                                        s["assembly"].get("audio_kbps", 192))

    lo, hi = s["episode"]["target_seconds"]
    timeline = {
        "episode_id": episode_id, "dry_run": voice.get("dry_run") or visuals.get("dry_run"),
        "total_seconds": round(length, 3), "story_seconds": round(total, 3), "within_target": lo <= total <= hi + 1,
        "signature": bool(sig), "loudness": measured,
        "music": music.name if music else None, "segments": segs, "shots": shot_rows,
        "output": final.name,
    }
    (rdir / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), "utf-8")
    return timeline
