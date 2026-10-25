"""The episode script format, shared by the generator, the validator and later phases."""

from __future__ import annotations

import re
import unicodedata
from typing import Literal

from pydantic import BaseModel, Field

Beat = Literal["hook", "story", "kural", "lesson", "tease"]


class Hook(BaseModel):
    style: Literal["question", "tense_moment", "surprising_line"]
    on_screen_ta: str = Field(description="Big on-screen Tamil text for 0–3 s, at most 6 words")
    narration_ta: str = Field(description="What the narrator says in 0–3 s")


class Segment(BaseModel):
    beat: Beat
    start_s: float
    end_s: float
    speaker: Literal["narrator", "thatha", "kavin", "other"]
    narration_ta: str = Field(description="Spoken Tamil for this segment, exactly as it should be voiced")
    on_screen_ta: str = Field(description="Extra on-screen Tamil text besides subtitles, or empty string")


class Shot(BaseModel):
    n: int
    beat: Beat
    start_s: float
    end_s: float
    characters: list[str] = Field(description="Character ids from the character sheet, e.g. thatha, kavin")
    location: str
    action_en: str = Field(description="What happens in the shot, in English")
    camera_en: str = Field(description="Framing and camera move, in English")
    image_prompt_en: str = Field(description="Prompt for the still image (first frame), no text in image")
    motion_prompt_en: str = Field(description="Prompt for the 4–8 s image-to-video clip")


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
    hooks: list[Hook]
    chosen_hook: int = Field(description="Index (0-based) of the hook used in the segments")
    segments: list[Segment]
    shots: list[Shot]
    lesson_ta: str = Field(description="One shareable lesson line, at most 12 words")
    tease_ta: str = Field(description="One line teasing the next kural without naming its answer")
    loop_note_en: str = Field(description="How the last frame and line flow back into the first")
    youtube: YouTubeMeta
    instagram: InstagramMeta


# ---- checks that structured output alone cannot guarantee ------------------

_MARKS = re.compile(r"[ா-்ௗ‌‍]")


def tamil_letters(text: str) -> int:
    """Letters as a reader sees them (consonant+vowel sign counts once)."""
    text = unicodedata.normalize("NFC", text)
    return sum(1 for ch in _MARKS.sub("", text) if "஀" <= ch <= "௿")


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
    order = ["hook", "story", "kural", "lesson", "tease"]
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
    if not any("thatha" in s.characters for s in script.shots) or not any("kavin" in s.characters for s in script.shots):
        errors.append("Thatha and Kavin must both appear on screen")

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
