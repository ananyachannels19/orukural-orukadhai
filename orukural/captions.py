"""On-screen Tamil text, burned in at render: one subtitle per spoken line, every line in the same
font, size, colour and position (hook, story, dialogue, kural and tease alike), and only one on screen
at a time. The words are what is heard, so reading and listening never disagree. Most Shorts are
watched muted, so this is not optional.

The text sits in the middle band: the bottom ~25% and the right edge are under YouTube's and
Instagram's buttons and caption."""
from __future__ import annotations

from pathlib import Path

from .config import Settings
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
