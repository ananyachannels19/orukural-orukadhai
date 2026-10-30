"""Per-shot picture edits, applied to a Flow clip before it is cut into the film.

`episodes/<id>/edit.json`, keyed by shot number (all seconds are the clip's, as Flow made it):

  {"6": {"cut": [[2.95, 4.25]]},
   "7": {"card": "kural"},
   "9": {"sharpen": {"box": [640, 380, 440, 720], "amount": 1.5}}}

- cut: drop stretches of the clip (Flow said or did something we don't use). Picture and sound go
  together, and each part after a cut is punched in a little (assembly.cut_punch) so the jump reads as
  a cut-in rather than a glitch.
- card: blur and dim the picture and show the kural (or the given lines) over it, in the subtitle
  font. For a shot where a character's mouth does not move with the words they say.
- sharpen: a gentle unsharp mask on one region, in 1080x1920 pixels, for a face Flow left soft.
- blur: hide fake text Flow drew (a number plate, a sign): [[from, to, x, y, w, h], ...], each a box in
  1080x1920 pixels blurred between those clip seconds; a moving object gets one box per short stretch.
- still: {"at": 0.25, "push": 1.04, "seconds": 3.75} holds the frame at `at` (a character not talking, the
  pose the film loops back to) with a slow push-in of `push` over `seconds`, instead of the moving clip;
  "direction": "out" eases from `push` back to the full frame, ending on exactly the clip's frame. The
  render's held-frame check allows it: the stillness is meant.

The edited clip is rendered once at the film's size; `to_clip` maps the original clip's seconds onto it
(for the speech spans pinned in lipsync.json)."""
from __future__ import annotations

import json
from pathlib import Path

from . import media
from .config import Settings
from .schema import EpisodeScript


def load(ep_dir: Path) -> dict[int, dict]:
    f = ep_dir / "edit.json"
    raw = json.loads(f.read_text("utf-8")) if f.exists() else {}
    return {int(k): v for k, v in raw.items() if k.isdigit()}


def episode_overrides(ep_dir: Path) -> dict:
    """edit.json's non-shot keys: this episode's own settings, e.g. {"kural": {"text_y": 430}} to place the
    verse where this episode's kural shot has no faces (the channel default stays in config.yaml)."""
    f = ep_dir / "edit.json"
    raw = json.loads(f.read_text("utf-8")) if f.exists() else {}
    return {k: v for k, v in raw.items() if not k.isdigit()}


def kept(cuts: list[list[float]], dur: float) -> list[tuple[float, float]]:
    """The stretches of a clip left after dropping `cuts`."""
    out, t = [], 0.0
    for a, b in sorted((max(0.0, a), min(dur, b)) for a, b in cuts):
        if a > t:
            out.append((t, a))
        t = max(t, b)
    if dur > t:
        out.append((t, dur))
    return out


def to_clip(parts: list[tuple[float, float]]):
    """Original clip seconds -> seconds in the clip made of `parts` (a time inside a cut lands on the cut)."""
    def move(t: float) -> float:
        before = 0.0
        for a, b in parts:
            if t < b:
                return before + max(0.0, t - a)
            before += b - a
        return before
    return move


def _card_png(s: Settings, lines: list[str], out: Path) -> Path:
    """The lines centred on a dark rounded panel, in the subtitle font, on a transparent 1080x1920 frame."""
    from PIL import Image, ImageDraw

    from .captions import _font, _wrap
    font, stroke = _font(s), 5
    im = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    lines = [row for x in lines for row in _wrap(draw, x, font, 900)]  # a kural line is often wider than the frame
    line_h = int(s["captions"]["size"] * 1.25)
    widths = [draw.textlength(x, font=font) for x in lines]
    w, h = min(1000, int(max(widths)) + 120), line_h * len(lines) + 90
    top = 760 - h // 2
    draw.rounded_rectangle((540 - w // 2, top, 540 + w // 2, top + h), radius=36, fill=(0, 0, 0, 150))
    for k, x in enumerate(lines):
        draw.text((540, top + 45 + k * line_h), x, font=font, anchor="ma", fill=(255, 236, 170, 255),
                  stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    im.save(out)
    return out


def _punch(s: Settings, p: float) -> str:
    """A punch-in by p about the logo badge's centre: Flow's sparkle stays where the badge covers it."""
    cover = s["assembly"].get("watermark_cover") or {}
    ax, ay = 540.0, 960.0
    if cover.get("image") and (s.root / cover["image"]).exists():
        from PIL import Image
        w, h = Image.open(s.root / cover["image"]).size
        ax, ay = cover["x"] + w / 2, cover["y"] + h / 2
    return (f",crop={1080 / p:.0f}:{1920 / p:.0f}:{ax * (1 - 1 / p):.0f}:{ay * (1 - 1 / p):.0f},"
            f"scale=1080:1920:flags=lanczos,setsar=1")


def _still(s: Settings, clip: Path, spec: dict, out: Path) -> list[tuple[float, float]]:
    """The clip's frame at spec["at"] held for the clip's whole length, pushing in slowly from `at` on (silent)."""
    from .assemble import _encode
    dur, at = media.duration(clip), spec.get("at", 0.0)
    frame = spec.get("frame", at)  # which frame to hold, when it is not where the push starts (e.g. the clip's last)
    push, span = spec.get("push", 1.04), spec.get("seconds", 4.0)
    prog = f"min(max(t-{at:.3f},0)/{span:.3f},1)"
    # "out": start pushed in and ease back to the full frame, so the last frame is the clip's own frame at
    # `at` (the loop back into the opening then matches exactly)
    z = f"({push:.4f}-{push - 1:.4f}*{prog})" if spec.get("direction") == "out" else f"(1+{push - 1:.4f}*{prog})"
    vf = (f"{media.fill_frame()},scale=w='ceil(1080*{z}/2)*2':h='ceil(1920*{z}/2)*2':eval=frame,"
          f"crop=1080:1920:(iw-1080)/2:(ih-1920)/2,setsar=1,fps={s['assembly']['fps']}")
    media.run(["-ss", f"{frame:.3f}", "-i", str(clip), "-frames:v", "1", str(out.with_suffix(".png"))])
    # the clip's own colour tags: a piece that differs mid-film makes ffmpeg rebuild the final filter graph,
    # and that stalled the signature overlay (K0788 v5.1 hung at the loop shot)
    tags = media.color_tags(clip)
    media.run(["-loop", "1", "-t", f"{dur:.3f}", "-i", str(out.with_suffix(".png")), "-vf", vf, *_encode(s),
               *tags, str(out)])
    return [(0.0, dur)]


def _render(s: Settings, clip: Path, spec: dict, card: Path | None, out: Path) -> list[tuple[float, float]]:
    from .assemble import _encode
    if spec.get("still"):
        return _still(s, clip, spec["still"], out)
    dur = media.duration(clip)
    parts = kept(spec.get("cut", []), dur)
    punch = s["assembly"].get("cut_punch", 1.12)
    has_audio = media.has_audio(clip)
    chain, ins = [], []
    for k, (a, b) in enumerate(parts):
        zoom = _punch(s, punch) if k % 2 else ""
        chain.append(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS,{media.fill_frame()}{zoom},"
                     f"fps={s['assembly']['fps']}[v{k}]")
        ins.append(f"[v{k}]")
        if has_audio:
            chain.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{k}]")
            ins.append(f"[a{k}]")
    chain.append(f"{''.join(ins)}concat=n={len(parts)}:v=1:a={1 if has_audio else 0}[cv]" + ("[ca]" if has_audio else ""))
    last, args = "cv", ["-i", str(clip)]
    if sh := spec.get("sharpen"):
        x, y, w, h = sh["box"]
        size = sh.get("size", 7)
        chain.append(f"[{last}]split[sa][sb];[sb]crop={w}:{h}:{x}:{y},unsharp={size}:{size}:{sh.get('amount', 1.5)}:5:5:0[sc];"
                     f"[sa][sc]overlay={x}:{y}[sh]")
        last = "sh"
    for k, (t0, t1, x, y, w, h) in enumerate(spec.get("blur", [])):
        chain.append(f"[{last}]split[ba{k}][bb{k}];[bb{k}]crop={w}:{h}:{x}:{y},boxblur=luma_radius=min(w\\,h)/3:luma_power=2:chroma_radius=min(cw\\,ch)/3:chroma_power=2[bc{k}];"
                     f"[ba{k}][bc{k}]overlay={x}:{y}:enable='between(t,{t0:.3f},{t1:.3f})'[bl{k}]")
        last = f"bl{k}"
    if card:
        args += ["-i", str(card)]
        chain.append(f"[{last}]gblur=sigma=22,eq=brightness=-0.10:saturation=0.8[bg];[bg][1:v]overlay=0:0[cd]")
        last = "cd"
    maps = ["-map", f"[{last}]"] + (["-map", "[ca]", "-c:a", "aac", "-b:a", "192k"] if has_audio else [])
    enc = [x for x in _encode(s) if x != "-an"]
    media.run([*args, "-filter_complex", ";".join(chain), *maps, *enc, str(out)])
    return parts


def prepare(s: Settings, ep_dir: Path, script: EpisodeScript, kural: dict | None, clips: dict[int, Path]
            ) -> tuple[dict[int, Path], dict]:
    """Apply edit.json to the clips it names. Returns the clips to use and, per edited shot, a function from the
    original clip's seconds to the edited clip's."""
    specs = load(ep_dir)
    if not specs:
        return clips, {}
    out_dir = ep_dir / "render" / "edit"
    out_dir.mkdir(parents=True, exist_ok=True)
    clips, moves = dict(clips), {}
    for n, spec in specs.items():
        if n not in clips:
            continue
        card = None
        if c := spec.get("card"):
            lines = [kural["verse"]["line1"], kural["verse"]["line2"]] if c == "kural" and kural else list(c)
            card = _card_png(s, lines, out_dir / f"card{n:02d}.png")
        out = out_dir / f"shot{n:02d}.mp4"
        parts = _render(s, clips[n], spec, card, out)
        clips[n], moves[n] = out, to_clip(parts)
    return clips, moves
