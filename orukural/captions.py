"""On-screen Tamil text, burned in at render: one subtitle per spoken line, every line in the same
font, size, colour and position (hook, story, dialogue, kural and tease alike). A long line is shown one
row at a time, each row timed across the voice in proportion to its length, so the text never grows
upwards into the picture and only one row is ever on screen. The words are what is heard, so reading and listening never disagree. Most Shorts are
watched muted, so this is not optional.

The text sits in the middle band: the bottom ~25% and the right edge are under YouTube's and
Instagram's buttons and caption."""
from __future__ import annotations

import re
import subprocess
from functools import lru_cache
from pathlib import Path

from . import media
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


WIDTH = 1080 - 2 * 90


def _row_times(rows: list[str], seconds: float, audio: Path | None) -> list[float]:
    """Start of each row and end of the last, in seconds into the line's voice file. Rows share out the
    time the voice is actually speaking (pauses left out) in proportion to their length; a split that
    lands right at a pause moves to the end of it, so the next row comes up as the voice resumes."""
    gaps = media.pauses(audio) if audio and audio.exists() else []
    onset = next((b for a, b in gaps if a <= 0.05), 0.0)
    stop = next((a for a, b in gaps if b >= seconds - 0.05 and a > onset), seconds)
    inner = [(a, b) for a, b in gaps if onset < a and b < stop]
    # each pause as (speech heard before it, start, end)
    marks, heard, prev = [], 0.0, onset
    for a, b in inner:
        heard += a - prev
        marks.append((heard, a, b))
        prev = b
    total = heard + stop - prev

    def at(x: float) -> float:  # speech time -> file time
        for h, a, b in marks:
            if x <= h:
                return a - (h - x)
        return stop - (total - x)

    # Voices pause at punctuation, so a row that ends on , ! ? or . takes the pause nearest its split;
    # the rows in between share out the speech between those pauses by length, and take a pause only
    # if one is left right at their split. Pause positions are counted in speech heard, not file time.
    weights = [len(r) for r in rows]
    cum = [sum(weights[:k + 1]) / sum(weights) * total for k in range(len(rows) - 1)]
    fixed: dict[int, tuple[float, float]] = {}  # split -> (speech heard, file time)
    free, last = list(marks), -1.0
    for k, row in enumerate(rows[:-1]):
        if not row.endswith((",", "!", "?", ".")):
            continue
        near = [m for m in free if m[0] > last and abs(m[0] - cum[k]) <= 0.6]
        if near:
            h, a, b = min(near, key=lambda m: abs(m[0] - cum[k]))
            fixed[k], last = (h, max(a, b - 0.1)), h
            free.remove((h, a, b))
    times = [onset]
    for k in range(len(rows) - 1):
        if k in fixed:
            t = fixed[k][1]
        else:
            lo = max([(j, fixed[j][0]) for j in fixed if j < k], default=(-1, 0.0))
            hi = min([(j, fixed[j][0]) for j in fixed if j > k], default=(len(rows) - 1, total))
            w0 = sum(weights[:lo[0] + 1])
            x = lo[1] + (hi[1] - lo[1]) * (sum(weights[:k + 1]) - w0) / (sum(weights[:hi[0] + 1]) - w0)
            near = [m for m in free if abs(m[0] - x) <= 0.25 and lo[1] < m[0] < hi[1]]
            t = max(near[0][1], near[0][2] - 0.1) if near else at(x)
        times.append(max(t, times[-1] + 0.3))
    return times + [max(stop, times[-1] + 0.3)]


def cues(s: Settings, script: EpisodeScript, segs: list[dict], total: float) -> list[tuple[str, float, float]]:
    """(row, start, end) for every subtitle row. segs: the real timeline from assemble.real_timeline
    (start/end/voice_seconds per line, and the voice file's path when it is known)."""
    from PIL import Image, ImageDraw
    font, probe, out = _font(s, strict=False), ImageDraw.Draw(Image.new("RGBA", (1, 1))), []
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        if not seg.narration_ta.strip():
            continue
        end = total if i == len(segs) - 1 else t["end"]
        rows = _wrap(probe, seg.narration_ta.strip(), font, WIDTH)
        times = _row_times(rows, t["voice_seconds"], Path(t["path"]) if t.get("path") else None)
        for k, row in enumerate(rows):
            a, b = t["start"] + times[k], t["start"] + times[k + 1]
            # the last row stays up for a short tail after the words, never into the next line
            out.append((row, a, min(end, b + 0.3) if k == len(rows) - 1 else b))
    return out


def write_ass(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out: Path) -> Path:
    c = s["captions"]
    lines = [HEADER.format(font=c["font"], size=c["size"], margin=c["margin"])]
    for row, a, b in cues(s, script, segs, total):
        lines.append(f"Dialogue: 0,{_ts(a)},{_ts(b)},Sub,,0,0,0,,{_text(row)}")
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


def _font(s: Settings, strict: bool = True):
    """strict: drawing needs raqm to shape Tamil; measuring rows for libass can make do without it."""
    from PIL import ImageFont, features
    raqm = features.check("raqm")
    if strict and not raqm:
        raise SystemExit("Pillow can't shape Tamil here (no libraqm), and this ffmpeg has no libass: install one "
                         "of them (`pip install --upgrade pillow` usually brings raqm) to burn in subtitles.")
    c = s["captions"]
    name = c.get("font_file", "NotoSansTamil-ExtraBold.ttf")
    path = next((d / c["fonts_dir"] / name for d in (s.root, ROOT) if (d / c["fonts_dir"] / name).exists()),
                s.root / c["fonts_dir"] / name)
    # libass sizes by line height, Pillow by em: 0.81 makes the two renders the same size
    return ImageFont.truetype(str(path), round(c["size"] * 0.81),
                              layout_engine=ImageFont.Layout.RAQM if raqm else ImageFont.Layout.BASIC)


def _wrap(draw, text: str, font, width: int) -> list[str]:
    """Rows that fit the width, breaking at the end of a phrase (after ! ? , or a full stop) where it
    can, so each row reads on its own, and between words only inside a phrase too long for one row."""
    fits = lambda r: draw.textlength(r, font=font) <= width
    rows, cur = [], ""
    # a stop ends a phrase only after a word, not inside an abbreviation like பி.டி.
    for phrase in re.split(r"(?<=[!?,])\s+|(?<=[^.\s]{3}\.)\s+", text):
        trial = f"{cur} {phrase}".strip()
        if fits(trial):
            cur = trial
            continue
        # a short start like "என்ன," runs on into the next phrase rather than flashing up alone
        if cur.endswith(("!", "?", ".")) or draw.textlength(cur, font=font) >= width / 2:
            rows.append(cur)
            cur = ""
        for word in phrase.split():
            trial = f"{cur} {word}".strip()
            if cur and not fits(trial):
                rows.append(cur)
                cur = word
            else:
                cur = trial
    return rows + ([cur] if cur else [])


def render_pngs(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out_dir: Path) -> list[tuple]:
    """For an ffmpeg without libass: each row drawn once to a transparent 1080-wide PNG, in the same
    font, size, outline and position as the ASS style. Returns (png, start, end, y) per row."""
    from PIL import Image, ImageDraw
    c, font = s["captions"], _font(s)
    out_dir.mkdir(parents=True, exist_ok=True)
    line_h, stroke, out = int(c["size"] * 1.1), 5, []
    for n, (row, a, b) in enumerate(cues(s, script, segs, total), 1):
        im = Image.new("RGBA", (1080, line_h + 2 * stroke), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((540, stroke), row, font=font, anchor="ma", fill=(255, 255, 255, 255),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        png = out_dir / f"sub{n:02d}.png"
        im.save(png)
        out.append((png, a, b, 1920 - c["margin"] - im.height))
    return out
