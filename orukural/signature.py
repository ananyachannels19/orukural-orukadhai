"""The channel signature, added to every episode by assemble. No Flow credits: everything is drawn here.

  badge flick  ~1 s: the ஒரு குறள் / ஒரு கதை badge pops in over the hook (never an intro before it),
               with a short bansuri phrase under the first line.
  olai reveal  at the kural (~25 s): the verse written on a palm leaf (olai) slides up and stays while
               the narrator says it.
  logo ending  ~2 s after the last line: the channel logo on the badge's brown, with a closing flute note.

`build()` makes the parts that never change once (assets/brand/signature/); the olai is drawn per
episode because it carries the kural. `studio.py signature` builds them and renders short previews.
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


def _encode_rgba(frames_dir: Path, out: Path) -> None:
    """PNG frames with transparency -> a .mov ffmpeg can overlay (png codec keeps the alpha)."""
    media.run(["-framerate", str(FPS), "-i", str(frames_dir / "f%03d.png"), "-c:v", "png", "-pix_fmt", "rgba", str(out)])


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


# ---- the three parts -------------------------------------------------------------------

def badge_flick(s: Settings, out: Path) -> Path:
    """~1 s: the badge flicks in (small, a little tilted, overshoots to full size), holds, then fades."""
    from PIL import Image
    c = _cfg(s).get("badge") or {}
    badge = Image.open(s.root / c.get("image", "assets/brand/badge.png")).convert("RGBA")
    width = c.get("width", 200)
    badge = badge.resize((width, round(badge.height * width / badge.width)), Image.LANCZOS)
    secs = c.get("seconds", 1.0)
    n = round(secs * FPS)
    box = (round(badge.width * 1.4), round(badge.height * 1.4))
    fdir = out.parent / "badge_frames"
    fdir.mkdir(parents=True, exist_ok=True)
    for k in range(n):
        t = k / FPS
        grow = _ease(t / 0.28)
        alpha = min(1.0, t / 0.12) * min(1.0, max(0.0, (secs - t) / 0.25))
        im = badge.resize((max(1, round(badge.width * (0.55 + 0.45 * grow))),
                           max(1, round(badge.height * (0.55 + 0.45 * grow)))), Image.LANCZOS)
        im = im.rotate(-12 * (1 - min(1.0, t / 0.28)), resample=Image.BICUBIC, expand=True)
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
        frame = Image.new("RGBA", box, (0, 0, 0, 0))
        frame.alpha_composite(im, ((box[0] - im.width) // 2, (box[1] - im.height) // 2))
        frame.save(fdir / f"f{k:03d}.png")
    _encode_rgba(fdir, out)
    return out


def olai_leaf(s: Settings, line1: str, line2: str, label: str, out: Path) -> Path:
    """The kural on a palm leaf: a long rounded strip, fibres, two string holes, ink-brown letters."""
    import random
    from PIL import Image, ImageDraw, ImageFilter
    W, H = 1000, 380
    rnd = random.Random(1330)
    leaf = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    for y in range(H):  # lighter along the middle rib, darker at the edges
        k = abs(y - H / 2) / (H / 2)
        col = tuple(int(a + (b - a) * k ** 1.6) for a, b in zip((226, 193, 128), (176, 132, 70)))
        d.line([(0, y), (W, y)], fill=col + (255,))
    for _ in range(140):  # fibres along the leaf
        y = rnd.randint(8, H - 8)
        x0 = rnd.randint(-200, W)
        shade = rnd.randint(120, 175)
        d.line([(x0, y), (x0 + rnd.randint(150, 600), y + rnd.choice((-1, 0, 1)))],
               fill=(shade, int(shade * 0.78), int(shade * 0.45), rnd.randint(40, 110)), width=1)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), radius=H // 2 - 40, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    leaf.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(leaf)
    d.rounded_rectangle((2, 2, W - 3, H - 3), radius=H // 2 - 40, outline=(120, 82, 38, 200), width=4)
    for hx in (W * 0.16, W * 0.84):  # string holes with a thread through
        d.ellipse((hx - 11, H / 2 - 11, hx + 11, H / 2 + 11), fill=(70, 45, 20, 255))
    ink = (58, 32, 12, 255)
    small = _font(s, 32, bold=False)
    d.text((W / 2, 34), label, font=small, anchor="ma", fill=(110, 70, 30, 255))
    size = 64
    while size > 34:  # the longer line fits between the holes
        font = _font(s, size)
        if max(d.textlength(x, font=font) for x in (line1, line2)) <= W * 0.64:
            break
        size -= 2
    d.text((W / 2, H / 2 - 12), line1, font=font, anchor="md", fill=ink)
    d.text((W / 2, H / 2 + 22), line2, font=font, anchor="ma", fill=ink)
    shadow = Image.new("RGBA", (W + 40, H + 40), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((20, 26, W + 18, H + 26), radius=H // 2 - 40, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    shadow.alpha_composite(leaf, (20, 20))
    out.parent.mkdir(parents=True, exist_ok=True)
    shadow.save(out)
    return out


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
    return out


def build(s: Settings, force: bool = False) -> dict[str, Path]:
    """The parts that are the same in every episode, made once."""
    d = out_dir(s)
    d.mkdir(parents=True, exist_ok=True)
    sa = (_cfg(s).get("flute") or {}).get("sa", 293.66)  # D, the bansuri's home note
    parts = {
        "badge": (d / "badge_flick.mov", lambda p: badge_flick(s, p)),
        # Mohanam: Sa Ga Pa Dha Sa' ... settling on Pa, under the hook's first words
        "flute_hook": (d / "flute_hook.wav", lambda p: flute_phrase([(0, 0.16), (4, 0.16), (7, 0.22), (9, 0.5)], sa, p)),
        "flute_end": (d / "flute_end.wav", lambda p: flute_phrase([(9, 0.3), (7, 0.3), (4, 0.3), (0, 0.9)], sa, p,
                                                                  tail=0.4, seed=8)),
        "ending": (d / "logo_ending.mp4", lambda p: logo_ending(s, p)),
    }
    for key, (path, make) in parts.items():
        if force or not path.exists():
            make(path)
    for tmp in ("badge_frames", "ending_frames"):
        for f in (d / tmp).glob("*.png"):
            f.unlink()
        if (d / tmp).exists():
            (d / tmp).rmdir()
    return {k: p for k, (p, _) in parts.items()}


# ---- into the film -------------------------------------------------------------------

def plan(s: Settings, kural: dict | None, segs: list[dict], total: float, work: Path) -> dict | None:
    """Where each part goes in this episode (real seconds), building what is missing."""
    if not enabled(s):
        return None
    parts = build(s)
    c = _cfg(s)
    kural_segs = [g for g in segs if g["beat"] == "kural"]
    out = {"badge": parts["badge"], "flute_hook": parts["flute_hook"], "flute_end": parts["flute_end"],
           "ending": parts["ending"], "ending_seconds": (c.get("ending") or {}).get("seconds", 2.0),
           "badge_xy": ((c.get("badge") or {}).get("x", 400), (c.get("badge") or {}).get("y", 150)),
           "flute_db": (c.get("flute") or {}).get("volume_db", -14), "total": total}
    if kural and kural_segs:
        leaf = olai_leaf(s, kural["verse"]["line1"], kural["verse"]["line2"], f"குறள் {kural['number']}",
                         work / "olai.png")
        start, end = kural_segs[0]["start"], kural_segs[-1]["end"]
        out["olai"] = {"image": leaf, "start": start, "end": end, "y": (c.get("olai") or {}).get("y", 1150)}
    return out


def video_graph(p: dict, last: str, first_input: int) -> tuple[list[str], str, str]:
    """(extra ffmpeg inputs, filter chain from [last], output label) for the badge, olai and logo ending."""
    ins, chain, k = [], [], first_input
    ins += ["-i", str(p["badge"])]
    bx, by = p["badge_xy"]
    chain.append(f"[{last}][{k}:v]overlay={bx}:{by}:eof_action=pass[sg1]")
    last, k = "sg1", k + 1
    if o := p.get("olai"):
        ins += ["-loop", "1", "-t", f"{o['end'] - o['start'] + 0.1:.3f}", "-i", str(o["image"])]
        a, rise = o["start"], 0.7
        chain.append(f"[{k}:v]format=rgba,fade=t=in:st=0:d=0.45:alpha=1,"
                     f"fade=t=out:st={max(0.0, o['end'] - a - 0.35):.3f}:d=0.35:alpha=1,setpts=PTS+{a:.3f}/TB[olai]")
        # slides up into place over `rise` seconds as it fades in
        chain.append(f"[{last}][olai]overlay=x=(W-w)/2:y='{o['y']}+if(lt(t-{a:.3f},{rise}),"
                     f"140*pow(1-(t-{a:.3f})/{rise},2),0)':eof_action=pass[sg2]")
        last, k = "sg2", k + 1
    ins += ["-i", str(p["ending"])]
    chain.append(f"[{last}]tpad=stop_mode=clone:stop_duration={p['ending_seconds']:.3f}[sg3]")
    chain.append(f"[{k}:v]setpts=PTS+{p['total']:.3f}/TB[end]")
    chain.append("[sg3][end]overlay=0:0:eof_action=pass[sg]")
    return ins, chain, "sg"


def audio_graph(p: dict, audio_label: str, first_input: int) -> tuple[list[str], list[str], str]:
    """(inputs, filters, label): the film's sound, the hook flute under it, the closing flute after it."""
    k = first_input
    ins = ["-i", str(p["flute_hook"]), "-i", str(p["flute_end"])]
    ms = int(p["total"] * 1000)
    chain = [f"[{audio_label}]apad=pad_dur={p['ending_seconds']:.3f}[sa0]",
             f"[{k}:a]aresample=48000,volume={p['flute_db']}dB[fh]",
             f"[{k + 1}:a]aresample=48000,volume={p['flute_db'] + 4}dB,adelay={ms}|{ms}[fe]",
             "[sa0][fh][fe]amix=inputs=3:normalize=0:duration=first[sa]"]
    return ins, chain, "sa"


def previews(s: Settings, kural: dict, background: Path | None, out: Path) -> list[Path]:
    """Three short mp4s to judge the signature by: the badge flick over the hook, the olai reveal, the ending."""
    parts = build(s)
    out.mkdir(parents=True, exist_ok=True)
    bg = ["-loop", "1", "-i", str(background)] if background else ["-f", "lavfi", "-i", f"color=c=0x6b5a48:s={media.W}x{media.H}"]
    fill = media.fill_frame()
    c = _cfg(s)
    bx, by = (c.get("badge") or {}).get("x", 400), (c.get("badge") or {}).get("y", 150)
    db = (c.get("flute") or {}).get("volume_db", -14)
    made = []
    f = out / "signature_badge_flick.mp4"
    media.run([*bg, "-i", str(parts["badge"]), "-i", str(parts["flute_hook"]), "-filter_complex",
               f"[0:v]{fill},fps={FPS}[b];[b][1:v]overlay={bx}:{by}:eof_action=pass[v];[2:a]volume={db + 10}dB[a]",
               "-map", "[v]", "-map", "[a]", "-t", "2.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(f)])
    made.append(f)
    leaf = olai_leaf(s, kural["verse"]["line1"], kural["verse"]["line2"], f"குறள் {kural['number']}", out / "olai.png")
    p = {"badge": parts["badge"], "badge_xy": (bx, -2000), "ending": parts["ending"], "ending_seconds": 0.0,
         "total": 4.0, "olai": {"image": leaf, "start": 0.5, "end": 4.0, "y": (c.get("olai") or {}).get("y", 1150)}}
    ins, chain, lab = video_graph(p, "b", 1)
    f = out / "signature_olai_reveal.mp4"
    media.run([*bg, *ins, "-filter_complex", f"[0:v]{fill},fps={FPS},trim=0:4.2[b];" + ";".join(chain),
               "-map", f"[{lab}]", "-t", "4.2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(f)])
    made.append(f)
    f = out / "signature_logo_ending.mp4"
    media.run(["-i", str(parts["ending"]), "-i", str(parts["flute_end"]), "-filter_complex", f"[1:a]volume={db + 10}dB[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(f)])
    made.append(f)
    return made
