"""On-screen Tamil text, burned in at render: one subtitle per spoken line. Two styles, so viewers can
tell who is talking: a character's line in plain white on the subtitle row; the narrator's line in
italic, a softer yellow, a little smaller and a little higher (`captions.narrator`). Only one subtitle is
ever on screen: when two lines overlap in time the earlier one is cut short where the next begins. A long line is shown one
row at a time, each row timed across the voice in proportion to its length, so the text never grows
upwards into the picture and only one row is ever on screen. The words are what is heard, so reading and listening never disagree. Most Shorts are
watched muted, so this is not optional.

The text sits in the middle band: the bottom ~25% and the right edge are under YouTube's and
Instagram's buttons and caption.

While the kural is on screen (the signature's kural reveal) there are no subtitles: the verse shown is
the subtitle for the narrator's line, and the slim leaf sits in the subtitle zone, so they never overlap.
When the verse leaves at a cut before the narrator finishes (`kural_until`), the rest of the line is subtitled.

Each segment's `on_screen_ta` (the hook card, the 10–12 s teaser, the last card) is drawn too, as a card
in the same font, centred in the lower third just above the subtitle row so the two never overlap, and
clear of the logo badge in the bottom-right corner. It stays up for its whole segment (the last card to
the end). Not while the verse is on screen.

A line a little too wide for one row (up to `captions.shrink_to_fit`, e.g. 1.25x) stays on one card, a
little smaller, rather than splitting a short shout like the hook in two."""
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
Style: Narr,{font},{narr_size},{narr_colour},{narr_colour},&H00000000,&H78000000,0,1,0,0,100,100,0,0,1,5,2,2,90,90,{narr_margin},1
Style: Card,{font},{card_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,5,2,2,90,90,{card_margin},1

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
            near = [m for m in free if abs(m[0] - x) <= 0.45 and lo[1] < m[0] < hi[1]]
            t = max(near[0][1], near[0][2] - 0.1) if near else at(x)
        times.append(max(t, times[-1] + 0.3))
    return times + [max(stop, times[-1] + 0.3)]


def narrator_style(s: Settings) -> dict:
    """How the narrator's subtitles differ from the characters': colour (RGB hex), italic, size, rise (px)."""
    c = s["captions"]
    n = {"colour": "#FFE08A", "italic": True, "scale": 0.92, "raise": 40, **(c.get("narrator") or {})}
    return {**n, "size": round(c["size"] * n["scale"]), "margin": c["margin"] + n["raise"]}


def _ass_colour(hexrgb: str) -> str:
    r, g, b = hexrgb.lstrip("#")[0:2], hexrgb.lstrip("#")[2:4], hexrgb.lstrip("#")[4:6]
    return f"&H00{b}{g}{r}".upper()


def cues(s: Settings, script: EpisodeScript, segs: list[dict], total: float) -> list[tuple[str, float, float]]:
    """(row, start, end) for every subtitle row, in time order, never two at once."""
    return [c[:3] for c in styled_cues(s, script, segs, total)]


def styled_cues(s: Settings, script: EpisodeScript, segs: list[dict], total: float
                ) -> list[tuple[str, float, float, bool]]:
    """(row, start, end, narrator) for every subtitle row."""
    return [c[:4] for c in word_cues(s, script, segs, total)]


def word_cues(s: Settings, script: EpisodeScript, segs: list[dict], total: float
              ) -> list[tuple[str, float, float, bool, list[float]]]:
    """(row, start, end, narrator, word starts) for every subtitle row: the karaoke highlight moves to each
    word at its start. segs: the real timeline from assemble.real_timeline (start/end/voice_seconds per line,
    and the voice file's path when it is known). Words are timed like rows: across the speech actually heard,
    by length, a word that ends a phrase taking the pause after it."""
    from PIL import Image, ImageDraw
    font, probe, out = _font(s, strict=False), ImageDraw.Draw(Image.new("RGBA", (1, 1))), []
    kural_on_screen = bool((s.raw.get("signature") or {}).get("enabled"))
    shrink = s["captions"].get("shrink_to_fit", 1.0)
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        under_verse = kural_on_screen and seg.beat == "kural"
        if not seg.narration_ta.strip() or (under_verse and not t.get("kural_until")):
            continue
        end = total if i == len(segs) - 1 else t["end"]
        text = seg.narration_ta.strip()
        rows = _wrap(probe, text, font, WIDTH)
        if len(rows) == 2 and probe.textlength(text, font=font) <= WIDTH * shrink:
            rows = [text]
        audio = Path(t["path"]) if t.get("path") else None
        times = _row_times(rows, t["voice_seconds"], audio)
        words = text.split()
        wt = _row_times(words, t["voice_seconds"], audio) if len(words) > 1 else [0.0, t["voice_seconds"]]
        first = 0
        for k, row in enumerate(rows):
            n = len(row.split())
            starts = [t["start"] + x for x in wt[first:first + n]]
            first += n
            a, b = t["start"] + times[k], t["start"] + times[k + 1]
            if under_verse:  # only the rows still being said once the verse has left
                if b < t["kural_until"] + 0.5:
                    continue
                a = max(a, t["kural_until"])
            # the last row stays up for a short tail after the words, never into the next line
            starts = [max(a, x) for x in starts] or [a]
            out.append((row, a, min(end, b + 0.3) if k == len(rows) - 1 else b, seg.speaker == "narrator", starts))
    # one subtitle at a time: a row ends where the next begins (lip sync can pull a line forward)
    out.sort(key=lambda c: c[1])
    for k in range(len(out) - 1):
        row, a, b, narr, ws = out[k]
        nxt = out[k + 1]
        if b > nxt[1]:
            b = max(nxt[1], a + 0.3)
            out[k] = (row, a, b, narr, ws)
            if nxt[1] < b:
                out[k + 1] = (nxt[0], b, max(nxt[2], b + 0.3), nxt[3], [max(b, x) for x in nxt[4]])
    return out


CARD_SNAP = 1.2  # a card whose slot starts this close before a shot cut waits for the cut


def card_cues(s: Settings, script: EpisodeScript, segs: list[dict], total: float, cuts: list[float] = ()
              ) -> list[tuple[list[str], float, float]]:
    """(rows, start, end) for every on-screen card: a segment's `on_screen_ta`, one row per line of it.
    cuts: the film's shot cuts; a card that would come up just before one waits for it, so it lands on the
    shot it belongs to (K0788's teaser came up over the last second of the key handover)."""
    kural_on_screen = bool((s.raw.get("signature") or {}).get("enabled"))
    out = []
    for i, (seg, t) in enumerate(zip(script.segments, segs)):
        rows = [r.strip() for r in (seg.on_screen_ta or "").splitlines() if r.strip()]
        if not rows:
            continue
        # from the start of the segment's slot, not of its voice (lip sync can start a line later); the last
        # card stays up to the end, under the closing call to action that follows it
        last = all(not (g.on_screen_ta or "").strip() for g in script.segments[i + 1:])
        a, end = (segs[i - 1]["end"] if i else 0.0), total if last else t["end"]
        if kural_on_screen and seg.beat == "kural":
            if not t.get("kural_until"):
                continue
            a = t["kural_until"]
        a = next((c for c in sorted(cuts) if a < c <= a + CARD_SNAP and c < end - 1.0), a)
        out.append((rows, a, end))
    return out


def card_layout(s: Settings) -> tuple[int, int]:
    """(font size, bottom margin) of the cards: a little bigger than subtitles, above the higher of the two
    subtitle rows (the narrator's) plus a gap."""
    c = s["captions"]
    size = c.get("card_size", c["size"] + 6)
    return size, narrator_style(s)["margin"] + round(c["size"] * 1.25) + 24


def write_ass(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out: Path,
              cuts: list[float] = ()) -> Path:
    c = s["captions"]
    card_size, card_margin = card_layout(s)
    n = narrator_style(s)
    lines = [HEADER.format(font=c["font"], size=c["size"], margin=c["margin"], card_size=card_size,
                           card_margin=card_margin, narr_size=n["size"], narr_margin=n["margin"],
                           narr_colour=_ass_colour(n["colour"]))]
    from PIL import Image, ImageDraw
    font, probe = _font(s, strict=False), ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    kara = karaoke_style(s)
    hexc = lambda rgba: _ass_colour("#%02X%02X%02X" % rgba[:3])
    for row, a, b, narr, starts in word_cues(s, script, segs, total):
        size = n["size"] if narr else c["size"]
        w = probe.textlength(row, font=font) * size / c["size"]
        fs = f"{{\\fs{int(size * WIDTH / w)}}}" if w > WIDTH else ""  # a one-card line a little too wide
        words = row.split()
        times = [a] + starts[1:len(words)] + [b] if kara["enabled"] else [a, b]
        lit = hexc(kara["narrator_word"] if narr else kara["word"])
        for j in range(len(times) - 1):
            if times[j + 1] - times[j] <= 0.01:
                continue
            text = " ".join(f"{{\\c{lit}}}{_text(x)}{{\\r}}" if k == j and kara["enabled"] else _text(x)
                            for k, x in enumerate(words))
            lines.append(f"Dialogue: 0,{_ts(times[j])},{_ts(times[j + 1])},{'Narr' if narr else 'Sub'},,0,0,0,,{fs}{text}")
    for rows, a, b in card_cues(s, script, segs, total, cuts):
        w = max(probe.textlength(r, font=font) for r in rows) * card_size / c["size"]
        fs = f"{{\\fs{int(card_size * WIDTH / w)}}}" if w > WIDTH else ""
        lines.append(f"Dialogue: 1,{_ts(a)},{_ts(b)},Card,,0,0,0,,{fs}{_text(chr(10).join(rows))}")
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


def _no_orphan(draw, rows: list[str], font, width: int) -> list[str]:
    """Never leave one word alone on the last row: move words down from the row above (as few as it takes,
    while that row keeps two or more and the last row still fits)."""
    rows = list(rows)
    while len(rows) > 1 and len(rows[-1].split()) == 1:
        above = rows[-2].split()
        moved = f"{above[-1]} {rows[-1]}"
        if len(above) < 3 or draw.textlength(moved, font=font) > width:
            break
        rows[-2], rows[-1] = " ".join(above[:-1]), moved
    return rows


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
    return _no_orphan(draw, rows + ([cur] if cur else []), font, width)


def render_pngs(s: Settings, script: EpisodeScript, segs: list[dict], total: float, out_dir: Path,
                cuts: list[float] = ()) -> list[tuple]:
    """For an ffmpeg without libass: each row drawn once to a transparent 1080-wide PNG, in the same
    font, size, outline and position as the ASS style. Returns (png, start, end, y) per row."""
    from PIL import Image, ImageDraw
    c, font = s["captions"], _font(s)
    out_dir.mkdir(parents=True, exist_ok=True)
    line_h, stroke, out = int(c["size"] * 1.1), 5, []
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    ns = narrator_style(s)
    small = font.font_variant(size=round(ns["size"] * 0.81))
    colour = tuple(int(ns["colour"].lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    kara = karaoke_style(s)
    pad = 24  # room for the shadow
    for n, (row, a, b, narr, starts) in enumerate(word_cues(s, script, segs, total), 1):
        base = small if narr else font
        w = probe.textlength(row, font=base)
        f = base.font_variant(size=int(base.size * WIDTH / w)) if w > WIDTH else base  # one-card line, shrunk
        words = row.split()
        plain, hi = (colour, kara["narrator_word"]) if narr else ((255, 255, 255, 255), kara["word"])
        # one picture per word: the row with that word lit (karaoke), shown from that word's start
        times = [a] + starts[1:len(words)] + [b] if kara["enabled"] else [a, b]
        for j in range(len(times) - 1):
            im = Image.new("RGBA", (1080, line_h + 2 * stroke + 2 * pad), (0, 0, 0, 0))
            lit = j if kara["enabled"] else -1
            _draw_words(im, words, f, (540, pad + stroke), plain, hi, lit, stroke)
            if narr and ns["italic"]:  # the font has no italic: slant it about the middle of the row
                k = 0.2
                im = im.transform(im.size, Image.AFFINE, (1, k, -k * im.height / 2, 0, 1, 0), Image.BICUBIC)
            png = out_dir / f"sub{n:02d}_{j:02d}.png"
            im.save(png)
            if times[j + 1] - times[j] > 0.01:
                out.append((png, times[j], times[j + 1],
                            1920 - (ns["margin"] if narr else c["margin"]) - im.height + pad))
    card_size, card_margin = card_layout(s)
    big = font.font_variant(size=round(card_size * 0.81))
    hook = script.segments[0].on_screen_ta.strip() if script.segments else ""
    for n, (rows, a, b) in enumerate(card_cues(s, script, segs, total, cuts), 1):
        if n == 1 and a < 0.05 and hook and c.get("hook_style") == "timestamp":
            out += _timestamp_card(s, rows, a, b, out_dir)
            continue
        row_h = int(card_size * 1.2)
        im = Image.new("RGBA", (1080, row_h * len(rows) + 2 * stroke + 2 * pad), (0, 0, 0, 0))
        for k, row in enumerate(rows):
            w = probe.textlength(row, font=big)
            f = big.font_variant(size=int(big.size * WIDTH / w)) if w > WIDTH else big
            _draw_words(im, [row], f, (540, pad + stroke + k * row_h), (255, 255, 255, 255), None, -1, stroke)
        png = out_dir / f"card{n:02d}.png"
        im.save(png)
        out.append((png, a, b, 1920 - card_margin - im.height + pad))
    return out


def karaoke_style(s: Settings) -> dict:
    """The word-by-word highlight (`captions.karaoke`): on/off, the dialogue's lit word, the narrator's."""
    k = {"enabled": True, "word": "#FFD54A", "narrator_word": "#FFFFFF", **(s["captions"].get("karaoke") or {})}
    rgba = lambda h: tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return {**k, "word": rgba(k["word"]), "narrator_word": rgba(k["narrator_word"])}


def _draw_words(im, words: list[str], font, top_centre: tuple[float, float], fill, lit_fill, lit: int,
                stroke: int, shadow: bool = True) -> None:
    """Words centred on one row, no background: a thin black outline and a soft drop shadow keep them
    readable on bright and dark frames alike; word `lit` (if any) in `lit_fill`."""
    from PIL import Image, ImageDraw, ImageFilter
    d = ImageDraw.Draw(im)
    space = d.textlength(" ", font=font)
    widths = [d.textlength(w, font=font) for w in words]
    x = top_centre[0] - (sum(widths) + space * (len(words) - 1)) / 2
    y = top_centre[1]
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        xs = x
        for w, ww in zip(words, widths):
            sd.text((xs + 3, y + 5), w, font=font, anchor="la", fill=(0, 0, 0, 170),
                    stroke_width=stroke + 2, stroke_fill=(0, 0, 0, 170))
            xs += ww + space
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    for k, (w, ww) in enumerate(zip(words, widths)):
        d.text((x, y), w, font=font, anchor="la", fill=lit_fill if k == lit else fill,
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        x += ww + space


def _timestamp_card(s: Settings, rows: list[str], a: float, b: float, out_dir: Path) -> list[tuple]:
    """The hook card as a film-title time stamp at the top left: the first line types on with a blinking
    cursor, the second fades in under it. Drawn as a few pictures, each shown for its moment."""
    from PIL import Image
    big, small = _font(s).font_variant(size=105), _font(s).font_variant(size=52)
    first, rest = rows[0], rows[1:]
    step, blink = 0.12, 0.2
    typed_at = a + 0.1 + step * len(first)
    out, t, k = [], a, 0
    while t < b - 0.01:
        n = min(len(first), int((t - a - 0.1) / step) + 1) if t >= a + 0.1 else 0
        cursor = int((t - a) / blink) % 2 == 0
        fade = 0.0 if t < typed_at + 0.2 else min(1.0, (t - typed_at - 0.2) / 0.4)
        im = Image.new("RGBA", (1080, 420), (0, 0, 0, 0))
        from PIL import ImageDraw
        d = ImageDraw.Draw(im)
        _draw_words(im, [first[:n] or " "], big, (70 + d.textlength(first[:n] or " ", font=big) / 2, 140), (255, 255, 255, 255),
                    None, -1, 5)
        if cursor:
            x = 70 + d.textlength(first[:n], font=big) + 14
            d.rectangle((x, 160, x + 12, 270), fill=(255, 255, 255, 235))
        if rest and fade > 0:
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            _draw_words(layer, rest, small, (76 + ImageDraw.Draw(layer).textlength(" ".join(rest), font=small) / 2, 290),
                        (255, 224, 138, 255), None, -1, 4)
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * fade)))
            im.alpha_composite(layer)
        png = out_dir / f"hook{k:02d}.png"
        im.save(png)
        nxt = min(b, t + (step if n < len(first) else 0.1 if fade < 1 else blink))
        out.append((png, t, nxt, 40))
        t, k = nxt, k + 1
    return out
