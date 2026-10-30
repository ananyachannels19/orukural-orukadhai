"""The episode script format, shared by the generator, the validator and later phases."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# No "next kural" tease: the lesson beat ends the episode with its card and loops to the hook.
Beat = Literal["hook", "story", "kural", "lesson"]


def _old_beat(v):
    """Scripts written before the tease was dropped: their last beat was "tease"; it is now part of the lesson."""
    return "lesson" if v == "tease" else v


class Hook(BaseModel):
    style: Literal["question", "tense_moment", "surprising_line"]
    on_screen_ta: str = Field(description="Big on-screen Tamil text for 0–3 s, at most 6 words")
    narration_ta: str = Field(description="What the narrator says in 0–3 s")


class Segment(BaseModel):
    beat: Beat
    _beat = field_validator("beat", mode="before")(_old_beat)
    start_s: float
    end_s: float
    speaker: str = Field(description="'narrator', or the id of a character in the episode's cast")
    narration_ta: str = Field(description="Spoken Tamil for this segment, exactly as it should be voiced")
    delivery: str = Field(default="", description="How the line is said, in English: calm, angry, teasing, tearful, "
                          "excited, whispered...; sent to the voice as its style")
    on_screen_ta: str = Field(description="Extra on-screen Tamil text besides subtitles, or empty string")


class CastMember(BaseModel):
    """One of the episode's own characters, invented for this story (see data/characters.yaml casting)."""
    id: str = Field(description="snake_case id used in shots and segments, e.g. vignesh")
    name_ta: str = Field(description="Name as the dialogue says it, in Tamil")
    age: int = Field(description="22-35 for adults; 4-15 for a child, only when the story needs one")
    job: str = Field(description="Specific everyday job, in English, e.g. bank clerk")
    look_en: str = Field(description="Face, hair, build, skin tone, glasses/beard: fixed for the episode")
    outfit_en: str = Field(description="What they wear for the whole episode")
    gender: Literal["male", "female"] = Field(description="Their voice must match: a male voice for a man")
    age_group: Literal["child", "adult", "elder"] = Field(
        default="adult", description="child (4-15), adult (22-35) or elder (50-80, a parent or grandparent)")
    personality: str = Field(default="", description="A few words on how they come across, e.g. calm, friendly; "
                             "used to pick their voice")
    voice: str = Field(default="", description="Gemini TTS voice (casting.voices). Leave empty: script-check picks one "
                       "by gender, age group and personality")
    voice_en: str = Field(default="", description="How they sound, in English, for Flow's lip-synced lines")
    voice_source: Literal["tts", "flow"] = Field(
        default="tts", description="tts: our voice fitted onto Flow's speech; flow: Flow's own voice from the clips")


class Location(BaseModel):
    id: str = Field(description="snake_case id; reuse a series location id from the world sheet when the scene is there")
    description_en: str = Field(description="Fixed look of the place: layout, materials, landmarks, colours")
    light_en: str = Field(description="Time of day and light for this episode, the same in every shot here")
    blocking_en: str = Field(description="Who is where and facing which way, so cuts between shots match")


class Prop(BaseModel):
    id: str = Field(description="snake_case id, e.g. puppy, red_backpack")
    name_ta: str = Field(default="", description="The Tamil word the dialogue uses for it, or empty")
    description_en: str = Field(description="Exact look: size, colour, markings, condition; never changes mid-episode")


class Outfit(BaseModel):
    character: str = Field(description="Character id")
    outfit_en: str = Field(description="What they wear for the whole episode, from the character sheet")


class Continuity(BaseModel):
    """The episode's fixed bible: every image and clip prompt is built from it."""
    locations: list[Location]
    props: list[Prop] = Field(description="Objects and animals that matter to the story or recur across shots")
    outfits: list[Outfit] = Field(description="One entry for every character on screen")


class Shot(BaseModel):
    n: int
    beat: Beat
    _beat = field_validator("beat", mode="before")(_old_beat)
    start_s: float
    end_s: float
    characters: list[str] = Field(description="Character ids from the episode's cast")
    location: str = Field(description="A location id from continuity.locations")
    props: list[str] = Field(default_factory=list, description="Prop ids from continuity.props visible in this shot")
    action_en: str = Field(description="What happens in the shot, in English")
    camera_en: str = Field(description="Framing and camera move, in English")
    image_prompt_en: str = Field(description="Composition, action, expressions and framing of the first frame. "
                                 "Character looks, outfits, location and props are added from the bible")
    motion_prompt_en: str = Field(description="Prompt for the 3–8 s image-to-video clip")
    motion_priority: int = Field(
        default=5, description="1 (clip made first, carries the story) to 5 (calm shot, made last)")
    clip_from: int | None = Field(
        default=None, description="Reuse an earlier shot's clip instead of making a new one (that shot's number)")
    clip_offset_s: float = Field(default=0.0, description="With clip_from: where in that clip this cut starts")


class YouTubeMeta(BaseModel):
    title: str = Field(description="Max 100 characters; starts with 'குறள் <number> |'")
    description_intro_ta: str = Field(description="2–3 line Tamil hook for the description; the template adds the rest")
    tags: list[str]
    pinned_comment_ta: str


class InstagramMeta(BaseModel):
    caption_ta: str = Field(description="Caption ending with one easy question to answer in comments")
    hashtags: list[str]


class EpisodeScript(BaseModel):
    kural_number: int
    story_title_ta: str
    story_title_en: str
    logline_en: str
    originality_note_en: str = Field(description="What in this story is new and specific to our series")
    meaning_ta: str = Field(description="Our own plain-Tamil meaning of the kural, 1–2 sentences")
    meaning_en: str = Field(description="Our own plain-English meaning, 1–2 sentences")
    cast: list[CastMember] = Field(default_factory=list, description="The episode's own 2–3 characters")
    thatha_cameo: bool = Field(default=False, description="Thatha (kumbakonam cast) appears as this family's "
                               "grandfather on a video call, on a phone or laptop screen in the shot")
    continuity: Continuity
    hooks: list[Hook]
    chosen_hook: int = Field(description="Index (0-based) of the hook used in the segments")
    segments: list[Segment]
    shots: list[Shot]
    lesson_ta: str = Field(description="One shareable lesson line, at most 12 words")
    tag_question_ta: str = Field(default="", description="One question asking viewers to tag a friend, partner or "
                                 "sibling, used in the caption, pinned comment and last card")
    loop_note_en: str = Field(description="How the last frame and line flow back into the first")
    youtube: YouTubeMeta
    instagram: InstagramMeta


# ---- checks that structured output alone cannot guarantee ------------------

_MARKS = re.compile(r"[ா-்ௗ‌‍]")


def tamil_letters(text: str) -> int:
    """Letters as a reader sees them (consonant+vowel sign counts once)."""
    text = unicodedata.normalize("NFC", text)
    return sum(1 for ch in _MARKS.sub("", text) if "஀" <= ch <= "௿")


# A posting day or time promised anywhere viewers read it ("new kural every Mon, Wed & Sat, 7:30 pm").
# A bare hour inside a story ("உங்க 3 AM நண்பன்") is fine; a clock time or a weekday is not.
SCHEDULE_WORDS = re.compile(
    r"\b(mon|tue|wed|thu|fri|sat|sun)(day|nesday|urday|sday)?\b|\b\d{1,2}[:.]\d{2}\s*(am|pm)?\b|\bIST\b"
    r"|திங்கள்|செவ்வாய்|புதன்|வியாழன்|வெள்ளிக்கிழமை|சனிக்கிழமை|சனி\s|ஞாயிறு",
    re.IGNORECASE)


def schedule_mentions(script: EpisodeScript) -> list[str]:
    """Text viewers read that names a posting day or time; we never promise one."""
    texts = {"youtube title": script.youtube.title, "description": script.youtube.description_intro_ta,
             "pinned comment": script.youtube.pinned_comment_ta, "instagram caption": script.instagram.caption_ta,
             "tag question": script.tag_question_ta}
    # the hook card may show the story's clock time ("3:04 AM", as a phone would); that is not a schedule
    texts.update({f"on-screen text at {g.start_s:g} s": re.sub(r"\d{1,2}:\d{2}\s*(AM|PM)", "", g.on_screen_ta)
                  if g.beat == "hook" else g.on_screen_ta for g in script.segments})
    return [f"{where}: {m.group(0)!r}" for where, text in texts.items() if (m := SCHEDULE_WORDS.search(text or ""))]


LATIN = re.compile(r"[A-Za-z]+(?:[ '-][A-Za-z]+)*")


def latin_words(script: EpisodeScript) -> list[str]:
    """Spoken lines and cards with English letters (the subtitles show what is written). Older scripts' "Save this"
    passes."""
    out = []
    for g in script.segments:
        for kind, text in (("narration", g.narration_ta), ("on-screen text", g.on_screen_ta.replace("Save this", ""))):
            text = re.sub(r"\[DRY RUN[^\]]*\]", "", text)  # the dry-run stub's placeholders
            text = re.sub(r"\d{1,2}:\d{2}\s*(AM|PM)\b", "", text)  # a clock time on a card, like a phone shows it
            out += [f"{kind} at {g.start_s:g} s: {m.group(0)!r}" for m in LATIN.finditer(text)]
    return out


NEXT_KURAL = re.compile(r"அடுத்த\s*குறள்|next\s+kural", re.IGNORECASE)


def next_kural_mentions(script: EpisodeScript) -> list[str]:
    """Lines or cards that point to the next kural; we dropped that tease for good."""
    texts = {f"{g.beat} at {g.start_s:g} s": g.narration_ta + "\n" + g.on_screen_ta for g in script.segments}
    texts.update({"lesson": script.lesson_ta, "loop note": script.loop_note_en})
    return [f"{where}: {m.group(0)!r}" for where, text in texts.items() if (m := NEXT_KURAL.search(text or ""))]


def _norm(s: str) -> str:
    return re.sub(r"[\s.,;:!?'\"‘’“”…\-–—]+", "", unicodedata.normalize("NFC", s))


def check(script: EpisodeScript, kural: dict, cfg: dict) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). Errors block the next phase; warnings are for the reviewer."""
    errors: list[str] = []
    warns: list[str] = []
    ep = cfg["episode"]
    lo, hi = ep["target_seconds"]
    smin, smax = ep["shots_per_episode"]
    hmin, hmax = cfg["script"]["hashtags"]

    if script.kural_number != kural["number"]:
        errors.append(f"kural_number is {script.kural_number}, expected {kural['number']}")
    if len(script.hooks) != cfg["script"]["hooks"]:
        errors.append(f"{len(script.hooks)} hooks, expected {cfg['script']['hooks']}")
    if not 0 <= script.chosen_hook < len(script.hooks):
        errors.append("chosen_hook is out of range")
    if not smin <= len(script.shots) <= smax:
        errors.append(f"{len(script.shots)} shots, expected {smin}–{smax}")

    segs = script.segments
    if not segs:
        errors.append("no segments")
        return errors, warns
    if segs[0].beat != "hook" or segs[0].start_s != 0:
        errors.append("first segment must be the hook starting at 0 s")
    for a, b in zip(segs, segs[1:]):
        if abs(a.end_s - b.start_s) > 0.05:
            errors.append(f"gap/overlap between segments at {a.end_s}s and {b.start_s}s")
    total = segs[-1].end_s
    if not lo <= total <= hi:
        errors.append(f"runtime {total:.1f}s is outside {lo}–{hi}s")
    order = ["hook", "story", "kural", "lesson"]
    seen = [s.beat for s in segs]
    if seen != sorted(seen, key=order.index):
        errors.append(f"beats out of order: {seen}")
    for beat in order:
        if beat not in seen:
            errors.append(f"missing beat: {beat}")
    struct = ep["structure"]
    hook_end = max(s.end_s for s in segs if s.beat == "hook")
    if hook_end > struct["hook"][1] + 0.5:
        warns.append(f"hook runs to {hook_end:.1f}s (target ≤ {struct['hook'][1]}s)")
    kural_start = min((s.start_s for s in segs if s.beat == "kural"), default=0)
    if not struct["kural"][0] - 4 <= kural_start <= struct["kural"][0] + 3:
        warns.append(f"kural starts at {kural_start:.1f}s (target ~{struct['kural'][0]}s)")

    hook = script.hooks[script.chosen_hook] if 0 <= script.chosen_hook < len(script.hooks) else None
    if hook and _norm(hook.narration_ta) not in _norm(segs[0].narration_ta):
        warns.append("first segment does not use the chosen hook's narration")

    verse = kural["verse"]["line1"] + kural["verse"]["line2"]
    kural_said = "".join(s.narration_ta for s in segs if s.beat == "kural")
    if _norm(verse) not in _norm(kural_said):
        errors.append("the kural segment does not contain the verse exactly as in kurals.json")

    # Narration pace: does the text fit the time it is given?
    lps = ep["narration_letters_per_second"]
    for s in segs:
        need = tamil_letters(s.narration_ta) / lps
        have = s.end_s - s.start_s
        if need > have * 1.25:
            warns.append(f"{s.beat} {s.start_s:.0f}–{s.end_s:.0f}s: ~{need:.1f}s of speech in {have:.1f}s")
    spoken = sum(tamil_letters(s.narration_ta) for s in segs) / lps
    if spoken > hi:
        errors.append(f"narration needs ~{spoken:.0f}s at {lps} letters/s, longer than {hi}s")

    for i, sh in enumerate(script.shots):
        if sh.n != i + 1:
            errors.append(f"shot numbering broken at shot {i + 1}")
        if sh.end_s - sh.start_s > 8:
            errors.append(f"shot {sh.n} is {sh.end_s - sh.start_s:.1f}s; clips are at most 8 s")
        if re.search(r"[஀-௿]", sh.image_prompt_en + sh.motion_prompt_en):
            errors.append(f"shot {sh.n}: image/motion prompts must not contain Tamil text")
    if script.shots and abs(script.shots[-1].end_s - total) > 0.5:
        errors.append(f"shots end at {script.shots[-1].end_s}s but narration ends at {total}s")
    for a, b in zip(script.shots, script.shots[1:]):
        if abs(a.end_s - b.start_s) > 0.05:
            errors.append(f"gap/overlap between shots {a.n} and {b.n}")
    by_n = {sh.n: sh for sh in script.shots}
    for sh in script.shots:
        if sh.clip_from is None:
            continue
        src = by_n.get(sh.clip_from)
        if not src or src.n >= sh.n or src.clip_from is not None:
            errors.append(f"shot {sh.n}: clip_from must name an earlier shot that has its own clip")
        elif sh.clip_offset_s + (sh.end_s - sh.start_s) > 8 + 0.05:
            errors.append(f"shot {sh.n}: reuses shot {src.n}'s clip from {sh.clip_offset_s:g} s, past its 8 s end")

    for where in schedule_mentions(script):
        errors.append(f"names a posting day or time ({where}); never promise a schedule")
    for where in latin_words(script):
        errors.append(f"English letters in {where}; write loanwords in Tamil script (bike → பைக்)")
    for where in next_kural_mentions(script):
        errors.append(f"teases the next kural ({where}); episodes end on their own lesson")
    if script.cast:  # the per-episode cast format (3 a week plan)
        if any(g.speaker != "narrator" for g in segs if g.beat == "kural"):
            errors.append("the narrator says the kural, over the lesson card")
        teaser = [g for g in segs if g.on_screen_ta.strip() and g.start_s <= 12 and g.end_s >= 10 and g.beat == "story"]
        if not teaser:
            warns.append("no one-line lesson teaser on screen at 10–12 s")
        cta = segs[-1]
        if cta.speaker != "narrator" or "டேக்" not in cta.narration_ta:
            warns.append("the last line should be the narrator's call to action: tag that kind of friend "
                         "(\"…டேக் பண்ணுங்க\")")
        if not any(g.on_screen_ta.strip() for g in segs if g.beat == "lesson"):
            warns.append("no lesson card (the short lesson line on screen at the end)")
        for g in segs:  # கால் alone reads as "leg": a phone call is அழைப்பு, or ஃபோன் கால் in speech
            for kind, text in (("narration", g.narration_ta), ("on-screen text", g.on_screen_ta)):
                if re.search(r"(?<!ஃபோன் )(?<!போன் )கால்(?![\u0B80-\u0BFF])", text):
                    warns.append(f"{kind} at {g.start_s:g} s: \"கால்\" alone reads as \"leg\"; for a phone call "
                                 f"write அழைப்பு (or ஃபோன் கால் where that is what is said)")
        if not script.tag_question_ta.strip():
            warns.append("no tag question (tag a friend, partner or sibling)")

    yt = script.youtube
    if len(yt.title) > 100:
        errors.append(f"YouTube title is {len(yt.title)} characters (max 100)")
    if not yt.title.startswith(f"குறள் {kural['number']}"):
        warns.append("YouTube title should start with 'குறள் <number>'")
    if sum(len(t) for t in yt.tags) + 2 * len(yt.tags) > 500:
        errors.append("YouTube tags exceed 500 characters")
    if not hmin <= len(script.instagram.hashtags) <= hmax:
        errors.append(f"{len(script.instagram.hashtags)} hashtags, expected {hmin}–{hmax}")
    if len(script.lesson_ta.split()) > 12:
        warns.append("lesson line is longer than 12 words")
    return errors, warns
