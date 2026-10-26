"""On-screen Tamil text, burned in at render: one subtitle per spoken line, every line in the same
font, size, colour and position (hook, story, dialogue, kural and tease alike), and only one on screen
at a time. The words are what is heard, so reading and listening never disagree. Most Shorts are
watched muted, so this is not optional.

The text sits in the middle band: the bottom ~25% and the right edge are under YouTube's and
Instagram's buttons and caption."""
from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path

from .config import ROOT, Settings
from .schema import EpisodeScript

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,5,2,2,90,90,{margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ts(t: float) -> str:
    cs = max(0, round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def _text(t: str) -> str:
    return t.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", "\\N").strip()


def write_ass(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out: Path) -> Path:
    """segs: the real timeline from assemble.real_timeline (start/end/voice_seconds per line)."""
    c = s["captions"]
    lines = [HEADER.format(font=c["font"], size=c["size"], margin=c["margin"])]
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        if not seg.narration_ta.strip():
            continue
        end = total if i == len(segs) - 1 else t["end"]
        # up for the spoken words plus a short tail, never into the next line
        sub_end = min(end, t["start"] + t["voice_seconds"] + 0.3)
        lines.append(f"Dialogue: 0,{_ts(t['start'])},{_ts(sub_end)},Sub,,0,0,0,,{_text(seg.narration_ta)}")
    out.write_text("\n".join(lines) + "\n", "utf-8")
    return out


def filter_arg(s: Settings, ass: Path) -> str:
    fonts = s.root / s["captions"]["fonts_dir"]
    esc = lambda p: str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"ass='{esc(ass)}':fontsdir='{esc(fonts)}'"


@lru_cache(maxsize=1)
def ffmpeg_has_ass() -> bool:
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return any(line.split()[1:2] == ["ass"] for line in out.splitlines() if line.strip())


def _font(s: Settings):
    from PIL import ImageFont, features
    if not features.check("raqm"):
        raise SystemExit("Pillow can't shape Tamil here (no libraqm), and this ffmpeg has no libass: install one "
                         "of them (`pip install --upgrade pillow` usually brings raqm) to burn in subtitles.")
    c = s["captions"]
    name = c.get("font_file", "NotoSansTamil-ExtraBold.ttf")
    path = next((d / c["fonts_dir"] / name for d in (s.root, ROOT) if (d / c["fonts_dir"] / name).exists()),
                s.root / c["fonts_dir"] / name)
    # libass sizes by line height, Pillow by em: 0.81 makes the two renders the same size
    return ImageFont.truetype(str(path), round(c["size"] * 0.81), layout_engine=ImageFont.Layout.RAQM)


def _wrap(draw, text: str, font, width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and draw.textlength(trial, font=font) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def render_pngs(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out_dir: Path) -> list[tuple]:
    """For an ffmpeg without libass: each subtitle drawn once to a transparent 1080-wide PNG, in the same
    font, size, outline and position as the ASS style. Returns (png, start, end, y) per line."""
    from PIL import Image, ImageDraw
    c, font = s["captions"], _font(s)
    out_dir.mkdir(parents=True, exist_ok=True)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    line_h, stroke, rows = int(c["size"] * 1.1), 5, []
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        if not seg.narration_ta.strip():
            continue
        end = total if i == len(segs) - 1 else t["end"]
        lines = _wrap(probe, seg.narration_ta.strip(), font, 1080 - 2 * 90)
        im = Image.new("RGBA", (1080, line_h * len(lines) + 2 * stroke), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for k, line in enumerate(lines):
            d.text((540, stroke + k * line_h), line, font=font, anchor="ma", fill=(255, 255, 255, 255),
                   stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        png = out_dir / f"sub{i + 1:02d}.png"
        im.save(png)
        rows.append((png, t["start"], min(end, t["start"] + t["voice_seconds"] + 0.3), 1920 - c["margin"] - im.height))
    return rows
