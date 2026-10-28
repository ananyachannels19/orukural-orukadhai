"""The channel signature, added to every episode by assemble. No Flow credits: everything is drawn here.
There is no intro: the hook opens the film, and the logo badge already sits in its corner over Flow's mark.

  kural reveal  while the narrator says the kural (~25 s), in one of two styles (signature.kural.style):
                slim_leaf  a thin, slightly see-through palm-leaf strip in the lower third (at most ~18% of
                           the frame's height, ~88% of its width), the verse in two lines; the story keeps playing
                clean_text the story dims to ~45% and the verse writes in line by line, white with a thin
                           gold underline, centred, a small குறள் N label above
  logo ending   ~2 s after the last line: the channel logo on the badge's brown, with a closing flute note.

`build()` makes the parts that never change once (assets/brand/signature/); the kural layers are drawn
per episode. `studio.py signature` builds them and renders short previews.
The flute is the same synthesised bansuri as tools/make_music.py, so it is ours like the music bed."""

from __future__ import annotations

import wave
from pathlib import Path

from . import media
from .config import Settings

FPS = 30
BROWN = (59, 49, 40)          # the badge's background
GOLD = (232, 196, 128)


def _cfg(s: Settings) -> dict:
    return s.raw.get("signature") or {}


def enabled(s: Settings) -> bool:
    return bool(_cfg(s).get("enabled"))


def out_dir(s: Settings) -> Path:
    return s.root / _cfg(s).get("dir", "assets/brand/signature")


def _font(s: Settings, size: int, bold: bool = True):
    from PIL import ImageFont, features
    name = "NotoSansTamil-ExtraBold.ttf" if bold else "NotoSansTamil.ttf"
    engine = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC
    return ImageFont.truetype(str(s.root / s["captions"]["fonts_dir"] / name), size, layout_engine=engine)


def _ease(x: float) -> float:
    """Ease-out with a small overshoot (a flick, not a slide)."""
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ---- sound ---------------------------------------------------------------------------
# The same bansuri as tools/make_music.py (sine with soft 2nd/3rd harmonics, breath, vibrato, gamaka
# glides), in plain Python so the pipeline needs no numpy; the room comes from ffmpeg's aecho.

SR = 44100


def _flute_note(f0: float, seconds: float, slide_from: float | None, rnd) -> list[float]:
    import math
    n = int(seconds * SR)
    out, phase, breath = [], 0.0, 0.0
    glide = int(0.12 * SR)
    for i in range(n):
        t = i / SR
        f = slide_from + (f0 - slide_from) * i / glide if slide_from and i < glide else f0
        f *= 1 + 0.006 * math.sin(2 * math.pi * 5.2 * t) * min(1.0, t / 0.4)
        phase += 2 * math.pi * f / SR
        breath = 0.97 * breath + 0.03 * rnd.gauss(0, 1)
        tone = math.sin(phase) + 0.18 * math.sin(2 * phase) + 0.06 * math.sin(3 * phase) + 0.25 * breath
        out.append(tone * min(1.0, t / 0.08) * min(1.0, (seconds - t) / 0.25))
    return out


def flute_phrase(notes: list[tuple[int, float]], sa: float, out: Path, tail: float = 0.6, seed: int = 5) -> Path:
    """A short bansuri phrase in Mohanam: (semitones above Sa, seconds) per note, with gamaka glides."""
    import array
    import random
    rnd = random.Random(seed)
    total = sum(d for _, d in notes) + tail
    x = [0.0] * int(total * SR)
    t, prev = 0.0, None
    for k, (semi, d) in enumerate(notes):
        f = sa * 2 ** (semi / 12)
        note = _flute_note(f, d * 1.1 if k < len(notes) - 1 else d + tail * 0.8, prev, rnd)
        i = int(t * SR)
        for j, v in enumerate(note[: len(x) - i]):
            x[i + j] += v
        prev, t = f, t + d
    peak = max(1e-9, max(abs(v) for v in x))
    raw = out.with_suffix(".dry.wav")
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(array.array("h", (int(v / peak * 0.8 * 32767) for v in x)).tobytes())
    media.run(["-i", str(raw), "-af", f"aecho=0.8:0.6:60|120:0.3|0.2,afade=t=out:st={max(0.0, total - 0.3):.3f}:d=0.3,"
               "aformat=channel_layouts=stereo", "-ar", str(SR), str(out)])
    raw.unlink()
    return out


# ---- the parts -----------------------------------------------------------------------

def _fit(s: Settings, d, lines: list[str], width: float, start: int, low: int, bold: bool = True):
    size = start
    while size > low:
        font = _font(s, size, bold)
        if max(d.textlength(x, font=font) for x in lines) <= width:
            return font
        size -= 2
    return _font(s, low, bold)


def slim_leaf(s: Settings, line1: str, line2: str, label: str, out: Path) -> Path:
    """Style A: a thin palm-leaf strip (~88% wide, ~16% high), slightly see-through, the verse in two lines."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    c = (_cfg(s).get("kural") or {})
    W, H = round(media.W * c.get("width", 0.88)), round(media.H * c.get("height", 0.16))
    rnd = random.Random(1330)
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    for y in range(H):  # lighter along the middle rib, darker at the edges
        k = abs(y - H / 2) / (H / 2)
        col = tuple(int(a + (b - a) * k ** 1.6) for a, b in zip((232, 204, 146), (190, 150, 90)))
        d.line([(0, y), (W, y)], fill=col + (255,))
    for _ in range(90):  # faint fibres along the leaf
        y = rnd.randint(6, H - 6)
        x0 = rnd.randint(-200, W)
        shade = rnd.randint(140, 185)
        d.line([(x0, y), (x0 + rnd.randint(150, 500), y)], fill=(shade, int(shade * 0.8), int(shade * 0.5),
                                                                  rnd.randint(25, 60)), width=1)
    alpha = round(255 * c.get("opacity", 0.88))
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 2, fill=alpha)
    leaf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    leaf.paste(body, (0, 0), mask.filter(ImageFilter.GaussianBlur(1)))
    d = ImageDraw.Draw(leaf)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=H // 2, outline=(122, 84, 40, 210), width=3)
    for hx in (H * 0.2, W - H * 0.2):  # the string holes at the two ends, clear of the words
        d.ellipse((hx - 7, H / 2 - 7, hx + 7, H / 2 + 7), fill=(80, 52, 24, 230))
    ink = (52, 28, 10, 255)
    d.text((H * 0.5, 14), label, font=_font(s, 26, bold=False), anchor="la", fill=(115, 74, 34, 255))
    font = _fit(s, d, [line1, line2], W - H * 0.8, 52, 32)
    d.text((W / 2, H / 2 + 2), line1, font=font, anchor="md", fill=ink)
    d.text((W / 2, H / 2 + 10), line2, font=font, anchor="ma", fill=ink)
    out.parent.mkdir(parents=True, exist_ok=True)
    leaf.save(out)
    return out


def clean_text(s: Settings, line1: str, line2: str, label: str, out_dir: Path) -> list[Path]:
    """Style B: two full-frame layers (label + line 1, then line 2): white ExtraBold, a thin gold underline each."""
    from PIL import Image, ImageDraw
    c = (_cfg(s).get("kural") or {})
    y0 = c.get("text_y", 820)
    out_dir.mkdir(parents=True, exist_ok=True)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = _fit(s, probe, [line1, line2], media.W * 0.86, 66, 40)
    gap = round(font.size * 1.9)
    layers = []
    for k, line in enumerate((line1, line2)):
        im = Image.new("RGBA", (media.W, media.H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if k == 0:
            d.text((media.W / 2, y0 - 70), label, font=_font(s, 34, bold=False), anchor="ms", fill=GOLD + (255,))
        y = y0 + k * gap
        d.text((media.W / 2, y), line, font=font, anchor="ms", fill=(255, 255, 255, 255),
               stroke_width=2, stroke_fill=(0, 0, 0, 120))
        w = d.textlength(line, font=font)
        d.line([(media.W / 2 - w * 0.42, y + 22), (media.W / 2 + w * 0.42, y + 22)], fill=GOLD + (230,), width=3)
        path = out_dir / f"kural_line{k + 1}.png"
        im.save(path)
        layers.append(path)
    return layers


def logo_ending(s: Settings, out: Path) -> Path:
    """~2 s: the logo grows in on the badge brown, the series name fades in under it."""
    from PIL import Image, ImageDraw
    c = _cfg(s).get("ending") or {}
    secs = c.get("seconds", 2.0)
    logo = Image.open(s.root / c.get("image", "assets/brand/logo_badge.png")).convert("RGBA")
    logo = logo.resize((560, round(logo.height * 560 / logo.width)), Image.LANCZOS)
    bg = Image.new("RGBA", (media.W, media.H), BROWN + (255,))
    d = ImageDraw.Draw(bg)
    for r in range(900, 0, -6):  # a soft warm glow behind the logo
        k = r / 900
        col = tuple(int(a + (b - a) * k) for a, b in zip((96, 74, 50), BROWN))
        d.ellipse((540 - r, 860 - r, 540 + r, 860 + r), fill=col + (255,))
    name, handle = _font(s, 76), _font(s, 40, bold=False)
    fdir = out.parent / "ending_frames"
    fdir.mkdir(parents=True, exist_ok=True)
    for k in range(round(secs * FPS)):
        t = k / FPS
        frame = bg.copy()
        g = 0.82 + 0.18 * _ease(t / 0.5)
        im = logo.resize((round(logo.width * g), round(logo.height * g)), Image.LANCZOS)
        im.putalpha(im.getchannel("A").point(lambda v: int(v * min(1.0, t / 0.3))))
        frame.alpha_composite(im, (540 - im.width // 2, 860 - im.height // 2))
        text = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(text)
        td.text((540, 1250), s["series"]["name_ta"], font=name, anchor="ma", fill=GOLD + (255,))
        td.text((540, 1370), s["series"]["youtube_handle"], font=handle, anchor="ma", fill=(240, 226, 200, 255))
        text.putalpha(text.getchannel("A").point(lambda v: int(v * min(1.0, max(0.0, (t - 0.35) / 0.4)))))
        frame.alpha_composite(text)
        frame.convert("RGB").save(fdir / f"f{k:03d}.png")
    media.run(["-framerate", str(FPS), "-i", str(fdir / "f%03d.png"), "-c:v", "libx264", "-crf", "16",
               "-pix_fmt", "yuv420p", str(out)])
    for f in fdir.glob("*.png"):
        f.unlink()
    fdir.rmdir()
    return out


def build(s: Settings, force: bool = False) -> dict[str, Path]:
    """The parts that are the same in every episode, made once: the logo ending and its flute."""
    d = out_dir(s)
    d.mkdir(parents=True, exist_ok=True)
    sa = (_cfg(s).get("flute") or {}).get("sa", 293.66)  # D, the bansuri's home note
    parts = {
        # Mohanam, Dha Pa Ga Sa: a falling phrase that settles home
        "flute_end": (d / "flute_end.wav", lambda p: flute_phrase([(9, 0.3), (7, 0.3), (4, 0.3), (0, 0.9)], sa, p,
                                                                  tail=0.4, seed=8)),
        "ending": (d / "logo_ending.mp4", lambda p: logo_ending(s, p)),
    }
    for path, make in parts.values():
        if force or not path.exists():
            make(path)
    return {k: p for k, (p, _) in parts.items()}


# ---- into the film -------------------------------------------------------------------

def kural_layers(s: Settings, kural: dict, start: float, end: float, work: Path) -> dict:
    """The kural reveal for one episode, in the configured style, between `start` and `end` (film seconds)."""
    c = _cfg(s).get("kural") or {}
    style = c.get("style", "slim_leaf")
    line1, line2, label = kural["verse"]["line1"], kural["verse"]["line2"], f"குறள் {kural['number']}"
    if style == "clean_text":
        return {"style": style, "layers": clean_text(s, line1, line2, label, work), "start": start, "end": end,
                "dim": c.get("dim", 0.45)}
    return {"style": "slim_leaf", "image": slim_leaf(s, line1, line2, label, work / "kural_leaf.png"),
            "start": start, "end": end, "y": c.get("y", 1150)}


def plan(s: Settings, kural: dict | None, segs: list[dict], total: float, work: Path) -> dict | None:
    """Where each part goes in this episode (real seconds), building what is missing."""
    if not enabled(s):
        return None
    parts = build(s)
    c = _cfg(s)
    kural_segs = [g for g in segs if g["beat"] == "kural"]
    out = {"flute_end": parts["flute_end"], "ending": parts["ending"],
           "ending_seconds": (c.get("ending") or {}).get("seconds", 2.0),
           "flute_db": (c.get("flute") or {}).get("volume_db", -14), "total": total}
    if kural and kural_segs:
        out["kural"] = kural_layers(s, kural, kural_segs[0]["start"], kural_segs[-1]["end"], work)
    return out


def _kural_graph(o: dict, last: str, k: int) -> tuple[list[str], list[str], str, int]:
    a, n = o["start"], o["end"] - o["start"]
    fade_out = f"fade=t=out:st={max(0.0, n - 0.35):.3f}:d=0.35:alpha=1"
    ins, chain = [], []
    if o["style"] == "clean_text":
        # dim the story while the verse is on screen, then write the lines in one after the other
        d = o["dim"]
        chain.append(f"[{last}]split[kb0][kb1];[kb1]colorchannelmixer=rr={d}:gg={d}:bb={d}[kdim];"
                     f"[kb0][kdim]overlay=0:0:enable='between(t,{a + 0.25:.3f},{o['end'] - 0.25:.3f})'[kd]")
        last = "kd"
        for j, layer in enumerate(o["layers"]):
            ins += ["-loop", "1", "-t", f"{n + 0.1:.3f}", "-i", str(layer)]
            delay = 0.3 + 0.7 * j
            chain.append(f"[{k}:v]format=rgba,fade=t=in:st={delay:.2f}:d=0.5:alpha=1,{fade_out},"
                         f"setpts=PTS+{a:.3f}/TB[kl{j}]")
            chain.append(f"[{last}][kl{j}]overlay=0:0:eof_action=pass[kt{j}]")
            last, k = f"kt{j}", k + 1
        return ins, chain, last, k
    ins += ["-loop", "1", "-t", f"{n + 0.1:.3f}", "-i", str(o["image"])]
    rise = 0.6
    chain.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.45:alpha=1,{fade_out},setpts=PTS+{a:.3f}/TB[leaf]")
    chain.append(f"[{last}][leaf]overlay=x=(W-w)/2:y='{o['y']}+if(lt(t-{a:.3f},{rise}),"
                 f"60*pow(1-(t-{a:.3f})/{rise},2),0)':eof_action=pass[kt]")
    return ins, chain, "kt", k + 1


def video_graph(p: dict, last: str, first_input: int) -> tuple[list[str], list[str], str]:
    """(extra ffmpeg inputs, filter chain from [last], output label) for the kural reveal and the logo ending."""
    ins, chain, k = [], [], first_input
    if o := p.get("kural"):
        i2, c2, last, k = _kural_graph(o, last, k)
        ins, chain = ins + i2, chain + c2
    ins += ["-i", str(p["ending"])]
    chain.append(f"[{last}]tpad=stop_mode=clone:stop_duration={p['ending_seconds']:.3f}[sg3]")
    chain.append(f"[{k}:v]setpts=PTS+{p['total']:.3f}/TB[end]")
    chain.append("[sg3][end]overlay=0:0:eof_action=pass[sg]")
    return ins, chain, "sg"


def audio_graph(p: dict, audio_label: str, first_input: int) -> tuple[list[str], list[str], str]:
    """(inputs, filters, label): the film's sound, then the closing flute under the logo ending."""
    ms = int(p["total"] * 1000)
    ins = ["-i", str(p["flute_end"])]
    chain = [f"[{audio_label}]apad=pad_dur={p['ending_seconds']:.3f}[sa0]",
             f"[{first_input}:a]aresample=48000,volume={p['flute_db'] + 4}dB,adelay={ms}|{ms}[fe]",
             "[sa0][fe]amix=inputs=2:normalize=0:duration=first[sa]"]
    return ins, chain, "sa"


def _caption_png(s: Settings, lines: list[tuple[str, int]], out: Path) -> Path:
    """Subtitle-style text (white, black outline, the captions font) at the captions' place, for previews."""
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (media.W, media.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = media.H - s["captions"]["margin"]
    for text, size in reversed(lines):  # bottom line sits on the captions' margin, the others above it
        # 0.81: the captions' libass size in Pillow's terms; shrink to fit inside the subtitle width
        font = _fit(s, d, [text], media.W - 180, round(size * 0.81), 28)
        d.text((media.W / 2, y), text, font=font, anchor="md", fill=(255, 255, 255, 255),
               stroke_width=5, stroke_fill=(0, 0, 0, 255))
        y -= round(size * 1.4)
    im.save(out)
    return out


def previews(s: Settings, kural: dict, background: Path | None, out: Path, before: str = "",
             lesson: str = "") -> list[Path]:
    """~7 s mp4s to judge the kural reveal by, one per style, each with a still of the full verse: a normal
    subtitle for 2 s, the kural with no subtitle, then 1 s of the lesson card. And the logo ending."""
    parts = build(s)
    out.mkdir(parents=True, exist_ok=True)
    if background and background.suffix.lower() in (".mp4", ".mov"):  # a clip: the story keeps playing under it
        bg = ["-stream_loop", "-1", "-i", str(background)]
    elif background:
        bg = ["-loop", "1", "-i", str(background)]
    else:
        bg = ["-f", "lavfi", "-i", f"color=c=0x6b5a48:s={media.W}x{media.H}"]
    fill = media.fill_frame()
    db = (_cfg(s).get("flute") or {}).get("volume_db", -14)
    size = s["captions"]["size"]
    sub = _caption_png(s, [(before or "சரோ இன்னும் பேசி முடிக்கல.", size)], out / "subtitle.png")
    card = _caption_png(s, [(lesson or "கூப்பிடாமலே வருபவன் தான் நண்பன்", size + 6), ("Save this", size - 8)],
                        out / "lesson_card.png")
    a, b, end = 2.0, 5.8, 7.0  # subtitle, kural, lesson card
    made = []
    for style, name in (("slim_leaf", "signature_kural_A_slim_leaf"), ("clean_text", "signature_kural_B_clean_text")):
        s.raw.setdefault("signature", {}).setdefault("kural", {})
        keep = s.raw["signature"]["kural"].get("style")
        s.raw["signature"]["kural"]["style"] = style
        o = kural_layers(s, kural, a, b, out / style)
        s.raw["signature"]["kural"]["style"] = keep
        k = 1
        ins = ["-loop", "1", "-t", f"{end}", "-i", str(sub), "-loop", "1", "-t", f"{end}", "-i", str(card)]
        chain = [f"[0:v]{fill},fps={FPS},trim=0:{end},setpts=PTS-STARTPTS[b0]",
                 f"[b0][{k}:v]overlay=0:0:enable='lt(t,{a - 0.05})'[b1]",
                 f"[b1][{k + 1}:v]overlay=0:0:enable='gte(t,{b})'[b]"]
        i2, c2, lab, _ = _kural_graph(o, "b", k + 2)
        f = out / f"{name}.mp4"
        media.run([*bg, *ins, *i2, "-filter_complex", ";".join(chain + c2), "-map", f"[{lab}]", "-t", f"{end}",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f)])
        still = out / f"{name}.png"
        media.run(["-ss", f"{a + 2.2:.2f}", "-i", str(f), "-frames:v", "1", str(still)])  # the full verse is up
        made += [f, still]
    f = out / "signature_logo_ending.mp4"
    media.run(["-i", str(parts["ending"]), "-i", str(parts["flute_end"]), "-filter_complex", f"[1:a]volume={db + 10}dB[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(f)])
    made.append(f)
    return made
