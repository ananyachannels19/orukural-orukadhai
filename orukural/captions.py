"""On-screen Tamil text, burned in at render: a subtitle for every spoken line, plus the script's
big on-screen text (hook, kural, lesson, tease). Most Shorts are watched muted, so this is not optional.

Everything stays in the upper two thirds: the bottom ~25% and the right edge sit under YouTube's and
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
Style: Sub,{font},{sub_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,4,1,2,90,90,{sub_margin},1
Style: Big,{bold_font},{big_size},&H005AD2FF,&H005AD2FF,&H00141414,&H64000000,0,0,0,0,100,100,0,0,1,6,2,8,80,80,{top_margin},1
Style: Kural,{bold_font},{kural_size},&H00D2ECFA,&H00D2ECFA,&H00102030,&HB4183048,0,0,0,0,100,100,0,0,3,18,0,8,70,70,{top_margin},1

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
    lines = [HEADER.format(**{k: c[k] for k in ("font", "bold_font", "sub_size", "big_size", "kural_size",
                                                "sub_margin", "top_margin")})]
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        end = total if i == len(segs) - 1 else t["end"]
        # One text on screen at a time: a line with big on-screen text (hook, kural, lesson, tease) shows that
        # instead of its subtitle, never both.
        if c.get("subtitles", True) and seg.narration_ta.strip() and not seg.on_screen_ta.strip():
            # the subtitle stays up for the spoken words plus a short tail, never into the next line
            sub_end = min(end, t["start"] + t["voice_seconds"] + 0.3)
            lines.append(f"Dialogue: 0,{_ts(t['start'])},{_ts(sub_end)},Sub,,0,0,0,,{_text(seg.narration_ta)}")
        if seg.on_screen_ta.strip():
            style = "Kural" if seg.beat == "kural" else "Big"
            lines.append(f"Dialogue: 1,{_ts(t['start'])},{_ts(end)},{style},,0,0,0,,{_text(seg.on_screen_ta)}")
    out.write_text("\n".join(lines) + "\n", "utf-8")
    return out


def filter_arg(s: Settings, ass: Path) -> str:
    fonts = s.root / s["captions"]["fonts_dir"]
    esc = lambda p: str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    return f"ass='{esc(ass)}':fontsdir='{esc(fonts)}'"
