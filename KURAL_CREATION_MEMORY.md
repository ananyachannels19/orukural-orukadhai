# KURAL CREATION MEMORY: ஒரு குறள் • ஒரு கதை (Orukural Orukadhai)

Knowledge base for the Thirukkural story reels project. It is written so that a local model (Gemma, Qwen, GPT-OSS on Ollama) can work on the project without any other context.

- **Written:** 2 Nov 2026, by Claude, at Ananya's request.
- **Sources:** every project thread about the reels (25 Oct to 2 Nov 2026), the project chat, the shared `kural-reel` skill, project memory, reports, and the live repo on Ananya's Mac (`/Users/ananya-24962/AI/Claude/orukural-studio`, read only).
- **Not covered:** the separate AI money channel project, which is left out on purpose.

## How to read this file

Every fact carries a status tag:

| Tag | Meaning |
|---|---|
| **[CONFIRMED]** | Ananya decided or approved it. Follow it. |
| **[DONE]** | Completed or published. |
| **[EXPERIMENT]** | Tried once. The result is noted, but it is not yet a rule. |
| **[FUTURE]** | An idea or plan, not built or not started. |
| **[UNRESOLVED]** | Open question, or two sources disagree. Ask Ananya. |
| **[SUPERSEDED]** | Was true once, replaced later. Do not follow. |
| **UNKNOWN** | The record does not say. Do not guess. |

Times are IST (UTC+5:30) unless marked UTC.

---

## 0. The 25 rules that matter most (read these first)

1. **[CONFIRMED] Never post without Ananya's clear go-ahead.** Posting is public and cannot be undone. A message ending in "?" is a question, not a go-ahead: on 30 Oct she edited "i want you to post it now" to "i want you to post it now?", and posting had to be stopped. "post now", "Post now" on a card, or "approved" are go-aheads.
2. **[CONFIRMED] Zero spend.** Use only free tools (Google Flow on her plan, free Gemini TTS, local FFmpeg) until the channel earns. Never silently switch to a paid tool.
3. **[CONFIRMED] Script, then stills, then clips.** Ananya approves the script first and the still images second. Only then are Flow video clips made, because clips cost credits.
4. **[CONFIRMED] Ask before any retry that costs credits.** Flow refusals and failed uploads cost nothing and can be retried freely.
5. **[CONFIRMED] Per-reel cap of 75 Flow credits** (about 7 clips). When credits are tight, stop and resume the next day rather than overspend (31 Oct: "stop it now and generate it tomorrow", "we dont have proper credits for it").
6. **[CONFIRMED] Download every clip from Flow at the 1080p upscale the first time.** Upscaling and downloading are free (0 credits). Never download the 720p file first.
7. **[CONFIRMED] Never put a "next kural" (அடுத்த குறள்) teaser at the end of any video** (rule from 29 Oct).
8. **[CONFIRMED] Never put a posting day, date or time anywhere viewers see it:** cards, titles, descriptions, captions or the pinned comment. Ananya removed the "🔔 புதிய குறள்: திங்கள், புதன், சனி" line herself.
9. **[CONFIRMED] Every story gets a new cast** of 2–3 people, mostly adults aged 22–35, built around a relatable bond (friends, couple, siblings, office). Most of her viewers are 25–34.
10. **[CONFIRMED] Child safety on screen.** Never show an adult shouting at, pointing at, grabbing or towering over a child. Show the child's reaction instead. Flow blocks such shots anyway.
11. **[CONFIRMED] Continuity is non-negotiable.** Same faces, outfits, props, places and light in every shot. Exactly one of each object, and no props appearing or vanishing. Ananya catches these errors, so check before she does.
12. **[CONFIRMED] Lip sync.** The speaker's mouth must be visible and moving during their line, and the voice must land on the mouth (speed change within about 0.9–1.1×).
13. **[CONFIRMED] Angry or scolding lines get "frowning, no smile"** in every prompt. Flow tends to add smiles.
14. **[CONFIRMED] Voice requests are scarce:** 10 free Gemini TTS requests a day, resetting at 12:30 IST. Send only the spoken words. A delivery note placed in the text gets read aloud.
15. **[CONFIRMED] Avoid a bare "கால்" meaning "call",** because it reads as "leg". Use "அழைப்பு", or "ஃபோன் கால்" if that is what is spoken.
16. **[CONFIRMED] Style defaults** (chosen 30 Oct on K0788):
    - H2 timestamp hook card ("3:04 AM" types on, then a second line).
    - Karaoke subtitles with no grey strip: outline and shadow, the spoken word lit yellow.
    - Narrator subtitles in soft yellow italic, never on screen together with dialogue subtitles.
    - Handwritten Kavivanar-font question and answer cards.
    - The kural shown as clean text on a dimmed frame.
    - A narrator line at the end asking viewers to tag someone.
    - Small round channel logo over Flow's watermark, and a logo ending.
17. **[CONFIRMED] No "save" text** ("சேவ் பண்ணுங்க" was removed). The ending asks viewers to tag a friend, partner or sibling instead.
18. **[CONFIRMED] Free sound effects, ambience and gentle zoom-in or zoom-out moves on real clips are allowed from K0100 onward** (31 Oct). Sounds must be licence-clear: they have been synthesised on her Mac. Motion is never faked on a single still image to replace a clip.
19. **[CONFIRMED] Final render:** 1080×1920, 30 fps, H.264 CRF 15, slow preset, AAC 320k, loudness −14 LUFS with true peak −1 dBTP. No frozen frames over 0.3 s, except the logo ending.
20. **[CONFIRMED] Use only the folder `/Users/ananya-24962/AI`.** Never touch `~/Documents` (rule from 2 Nov 2026, after she moved the project there).
21. **[CONFIRMED] AI disclosure everywhere.** YouTube "Altered or synthetic content" = Yes. Instagram "Add AI label" ON before Share, because it cannot be added on the web afterwards. The description line is: "This video uses AI-generated visuals and an AI narrator voice. Story, script and meaning are original to this channel."
22. **[CONFIRMED] Report progress proactively every 2–3 minutes during long work.** Ananya should never have to ask "?", "update" or "is it done". Long silences were her biggest complaint.
23. **[CONFIRMED] Find flaws yourself before showing a cut.** She said "you must check it right? i cannot remind you". When she asks to "find flaws", go frame by frame and list them with timestamps.
24. **[CONFIRMED] Never ask for or type passwords.** Ananya signs in herself. She once offered her login details and was told not to send them.
25. **[CONFIRMED] Check the kural text against `data/kurals.json` every time** (verse, meaning, adhikaram). The meanings are the channel's own words and must not copy any published commentary.

---

## A. Project overview, vision, audience, culture, strategy

### What it is
- **[CONFIRMED]** Channel name: **ஒரு குறள் • ஒரு கதை** ("Orukural Orukadhai", meaning "One Kural, One Story"). The handle is **@orukural.orukadhai** on both YouTube and Instagram. YouTube: https://www.youtube.com/@orukural.orukadhai
- **[CONFIRMED]** Format: vertical 9:16 Tamil Shorts and Reels, 35–45 s, 1080×1920. Each reel turns one Thirukkural verse into a short, original, modern story, and the kural lands as the answer to that story.
- **[CONFIRMED]** Owner and decision-maker: **Ananya** (account anusatheesh1905). Her Mac is an Apple M4 Pro with 24 GB of memory, machine name ananya-24962.

### Vision and long-term strategy
- **[CONFIRMED]** The goal is a channel that earns: the YouTube Partner Programme and monetisation. Everything stays zero-spend until the channel earns.
- **[FUTURE]** Eventually cover all 1330 kurals.
- **[FUTURE]** An 8–10 minute compilation per adhikaram.
- **[FUTURE]** A monthly kids' special with the original Thatha and Kavin cast ("kumbakonam" cast). It is configured but has not been made.
- **[FUTURE]** Placeholders exist in `config.yaml` for a link-in-bio, an ebook, merch and memberships. Their content is UNKNOWN.
- **[CONFIRMED]** Cadence: 3 reels a week as an internal target (Mon, Wed, Sat, 7 pm IST in config). It is never promised to viewers. In practice posts have gone up whenever ready and approved: Tue 27 Oct, Fri 30 Oct, Mon 2 Nov, with Wed 4 Nov planned.
- **[SUPERSEDED]** The first spec (25 Oct) was 3 Shorts a week on Mon/Wed/Sat at 7:30 pm, adhikaram by adhikaram in order, with recurring characters Thatha and Kavin. It was replaced on 28 Oct by relationship-led stories with new casts, with kurals chosen by theme rather than in order.
- **[UNKNOWN]** Plan document title: the plan file is called "Orukural Orukadhai 4 reels a week plan.md", but its heading says "3 reels a week plan". It is dated 28 Oct.

### Audience
- **[CONFIRMED]** Viewers are mostly aged 25–34. Ananya asked for stories about friends, love and relationships that this group relates to, not stories grouped by paal.
- **[CONFIRMED]** Language target: simple, warm Tamil that a 12-year-old in Tamil Nadu, Sri Lanka or Singapore understands. Dialogue is natural spoken Tamil.
- **[UNKNOWN]** Detailed demographics (geography, gender split). Instagram's web view did not show them.

### Tamil culture in the stories
- **[CONFIRMED]** Setting: Tamil Nadu today, in towns and cities. Typical places are homes, offices, hospitals, bus stands, tea shops, two-wheeler workshops and temple streets.
- **[CONFIRMED]** The visual palette is terracotta, turmeric yellow, neem green, temple-lamp gold and indigo night.
- **[DONE]** Cultural details used so far: lungi and banian, auto-rickshaw, filter coffee in a steel tumbler, a Deepavali kolam with diyas, blouse stitching at home, a town-bus conductor's night shift.
- **[CONFIRMED]** No real people, brands, politics, religious conflict, or violence beyond a raised voice. Illness is shown calmly: no blood, tubes or medical close-ups.

---

## B. Thirukkural content strategy

### Selecting kurals
- **[CONFIRMED]** Kurals are picked by relationship theme, not in paal order. Each episode in `config.yaml` has a `{kural, relationship}` pair. `data/themes.yaml` maps each of the 133 adhikarams to a theme tag (for example 31 = anger, 79 = friendship, 133 = love) and a relationship default (friends, couple, love, siblings, office, colleagues, family, neighbours, strangers).
- **[CONFIRMED]** The lineup agreed on 28 Oct, in order:

| Kural | Bond | Status |
|---|---|---|
| 788 | friends | **[DONE]** posted |
| 1330 | couple | **[DONE]** posted |
| 100 | siblings | **[DONE]** final ready, posting Wed 4 Nov |
| 467 | office | **[FUTURE]** next |
| 785 | friends | **[FUTURE]** |
| 1100 | love | **[FUTURE]** |
| 190 | colleagues | **[FUTURE]** |
| 104 | friends | **[FUTURE]** |

- **[EXPERIMENT]** K0301 (anger, adhikaram 31 வெகுளாமை) was the first pipeline episode, made in the old Thatha and Kavin format.

### Verse source
- **[DONE]** `data/kurals.json` holds all 1330 verses, built from 2 public sources. 1305 matched exactly and 25 were fixed by hand. Verses 143, 208, 666 and 689 were flagged, and Ananya confirmed them.
- **[CONFIRMED]** Copy the verse text exactly, with the same spelling. Use `data/verse_overrides.yaml` for overrides (K0301 uses "override:B").
- **[CONFIRMED]** `data/pronunciation_fixes.yaml` can respell words for the voice model only; subtitles keep the original spelling. It is currently empty.

### Turning a kural into a story
- **[CONFIRMED]** It must be one specific, surprising, emotionally true little situation about a real bond, set today, and never a retelling of a folk tale.
- **[CONFIRMED]** One person makes the mistake or faces the problem. The wiser one asks a question instead of lecturing, and the realisation belongs to the other person.
- **[CONFIRMED]** The kural arrives at about 25–35 s, spoken only by the narrator (Charon) and shown on screen. A short explanation in everyday Tamil may follow it.
- **[CONFIRMED]** A one-line lesson teaser goes on screen at 10–12 s, phrased as the question card. The analytics showed viewers leaving at about 12.7 s, before the kural.
- **[CONFIRMED]** It ends on one short lesson line worth screenshotting (the answer card), then a narrator line asking viewers to tag someone.
- **[CONFIRMED]** It loops: the last shot mirrors the first, so a replay flows straight on.
- **[CONFIRMED]** Meanings (`meaning_ta`, `meaning_en`) are the channel's own plain explanation and must not copy Parimelazhagar, Mu. Varadarasanar, Solomon Pappaiah, Kalaignar, Pope or others.

### Emotion
- **[CONFIRMED]** Open on a tense moment or a direct question at frame one. No greeting, no intro, no channel name. Kural #001 lost 45% of Instagram viewers in the first 3 s with a slow start.
- **[CONFIRMED]** Something should happen visibly every 2–3 s.
- **[DONE]** Emotional arcs used so far:
  - Panic, then relief and gratitude, ending on a joke (K0788).
  - A sulk, a playful peace offering, then laughter (K1330).
  - Hurt from a harsh word, then seeing again and softening (K0100).

### Family-friendly and child-friendly rules
- **[CONFIRMED]** At most one child (aged 4–15) and at most one elder (aged 50–80) per episode, and only when the story needs them.
- **[CONFIRMED]** No adult aggression toward a child on screen. Animals are safe and unharmed.
- **[CONFIRMED]** Thatha and Kavin may appear only in the monthly kids' special, or as a video-call cameo on a phone or laptop screen (`thatha_cameo: true`).

### Tamil dialogue rules
- **[CONFIRMED]** Natural spoken Tamil for each relationship: friends use first names and "டா/டி", colleagues say "sir/madam" or "அண்ணா/அக்கா", couples use their own pet forms. Each character keeps the same form of address all episode.
- **[CONFIRMED]** English loanwords only where people really use them, and always written in Tamil script (பேங்க், ஆபீஸ், போன், பெர்மிஷன்). No English letters on screen.
- **[CONFIRMED]** Pace: about 11 Tamil letters per second of speech. Silence and reaction shots are fine.
- **[CONFIRMED]** No bare "கால்" for "call" (see rule 15). `script-check` warns about it.
- **[CONFIRMED]** Ending tag lines are split evenly over two lines, never leaving one word alone (for example "அப்படிப்பட்ட உங்க ஃப்ரெண்ட்-அ" / "டேக் பண்ணுங்க!").

---

## C. Scriptwriting

### Format
- **[CONFIRMED]** Claude writes scripts in the chat session (`script.provider: session`), at zero cost. The output is `episodes/KNNNN/script.json`, validated by `prompts/episode_script.schema.json`, plus a readable `script.md`. The writer's instructions are in `prompts/script_system.md`, and `data/lessons_learned.md` is injected into every script prompt.
- **[CONFIRMED]** Beat timeline (35–45 s):

| Time | Beat | Content |
|---|---|---|
| 0–3 s | hook | A tense moment or a question, with big text on screen (the H2 timestamp card). |
| 3–25 s | story | One problem. The question card appears at 10–12 s. |
| 25–35 s | kural | The narrator says the verse slowly. |
| 35–43 s | lesson | The answer card, then the about 2.5 s tag-a-friend line. Then the loop. |

- **[CONFIRMED]** Write 3 hooks (question, tense_moment, surprising_line) and choose the strongest.
- **[CONFIRMED]** `script.json` fields include: `kural_number`, `story_title_ta` and `_en`, `logline_en`, `originality_note_en`, `meaning_ta` and `_en`, `cast`, `thatha_cameo`, `continuity` (locations, props, light, blocking), `hooks`, `chosen_hook`, `segments`, `shots`, `lesson_ta`, `tag_question_ta`, `loop_note_en`, `youtube`, `instagram`.

### Scene count and length
- **[CONFIRMED]** Aim for about 7 Flow clips per reel, mixing 8 s clips (12 credits each) and 4 s clips (7 credits each). One clip can serve two cuts (`clip_from`, `clip_offset_s`).
- **[DONE]** Actual counts:

| Episode | Clips | Credits | Length |
|---|---|---|---|
| K0301 | 10 | 97 | 45 s |
| K0788 | about 9 shots | about 146 on 29 Oct, plus remakes | 45.8 s |
| K1330 | 7 | 78 + 24 for remakes = 102 | 46 s |
| K0100 | 8 | 71 | 44.7 s |

### Characters and consistency
- **[CONFIRMED]** Each cast member has these fields:
  - `id`, `name_ta`, `age`, `job`, `gender`, `age_group`, `personality`
  - `look_en`, which fixes face, hair, build, skin and glasses or beard
  - `outfit_en`, one outfit for the whole episode
  - `voice` (Gemini TTS) and `voice_en` (a description for Flow)
- **[CONFIRMED]** Looks must differ from recent episodes in at least two of: face shape, hair, build, skin tone, glasses or beard. Names, looks and voices are not reused within 12 episodes (`data/cast_log.yaml`).
- **[DONE]** Casts so far (from `data/cast_log.yaml`):

| Episode | Character | Age, role | Look | Voice |
|---|---|---|---|---|
| K0301 | Thatha (Sundaram) | 72, retired Tamil teacher | Silver hair, white beard, round steel glasses | Algenib |
| K0301 | Kavin | 10 | Messy hair with a cowlick, gap in front teeth | Leda |
| K0788 | Vignesh | 29, bank clerk | Lean, oval face, side-parted hair, thin black rectangular glasses | Achird |
| K0788 | Saro | 29, auto mechanic | Stocky, curly hair, full short beard, scar through left eyebrow; maroon vest, green-and-white checked lungi | Enceladus |
| K0788 | Appa (Saro's father) | 62, retired lorry driver | Thin, grey stubble | Sadaltager |
| K1330 | Kathir | 30, pharmacist | Tall, crew cut, thick moustache, dimple | Iapetus |
| K1330 | Mithra | 27, runs a blouse-stitching business at home | Round face, long plait, gold nose stud, black bindi | Kore |
| K0100 | Muthu | 28, town-bus conductor | Sturdy, wavy hair, mole on left cheek, tired eyes | Alnilam |
| K0100 | Kayal | 22, final-year B.Com student | Half ponytail, red bindi, silver jhumkas | Autonoe |

- **[CONFIRMED]** Saro's appa in K0788 was added at Ananya's request.
- **[CONFIRMED]** The narrator is always **Charon**, and only the narrator says the kural.
- **[CONFIRMED]** Voices match gender and age. No voice-trial requests are spent; voices are picked from the table in `data/characters.yaml` by character, gender and emotion.

### Pronunciation
- **[CONFIRMED]** Shape the voice with punctuation (commas, "...", "!", "?") rather than notes. For example, the slower K0100 take was written "மயில்... ரொம்ப... அழகா இருக்கு, கயல்."
- **[DONE]** A pitch check runs on every line: adult male about 85–165 Hz, child above 170 Hz.
- **[DONE]** whisper.cpp transcribes each cut and compares it with the script, so every line is heard once and in Tamil.

### Subtitles
- **[CONFIRMED]** Font: Noto Sans Tamil ExtraBold, size 52, 400 px above the bottom edge (clear of the Shorts and Reels buttons). This was Ananya's choice on K0301.
- **[CONFIRMED]** Karaoke style: dialogue words are white with the current word in yellow (#FFD54A). Narrator text is soft yellow (#FFE08A) italic, scaled to 0.92. There is no background strip, only an outline and shadow.
- **[CONFIRMED]** Narrator and dialogue subtitles are never on screen at the same time. Subtitles are off while the kural shows.
- **[CONFIRMED]** Two-line subtitles are balanced by default.

### Real accepted scripts (Tamil, as approved)

**K0788, "3 மணிக்கு வந்த நண்பன்" (The friend at the gate at 3 am). Kural 788, adhikaram 79 நட்பு, பொருட்பால். [DONE]**

Verse: உடுக்கை இழந்தவன் கைபோல ஆங்கே / இடுக்கண் களைவதாம் நட்பு.

| Time | Who | Line | On screen |
|---|---|---|---|
| 0–3 s | Saro (panicked) | விக்கி... அப்பாவுக்கு மூச்சு விட முடியலடா! | 3:04 AM / ஒரு அழைப்பு. |
| 3–8 s | Narrator | சரோ இன்னும் பேசி முடிக்கல. அதுக்குள்ள, கேட்டுல ஒரு பைக் வெளிச்சம். | |
| 8–11 s | Vignesh | சாவியக் குடு. நீ அப்பா கூட இரு. | |
| 11–16 s | Narrator | விக்னேஷ் ஆட்டோ ஓட்டினான். பின்னால, அப்பாவ தாங்கிக்கிட்டு சரோ. | Question card: கூப்பிடும் முன்னே வருபவன் யார்? |
| 16–19 s | Narrator | சரோ கேக்கும் முன்னே, பணமும் கட்டிட்டான். | |
| 19–22 s | Saro | நான் உன்னக் கூப்பிடவே இல்லையேடா... | |
| 22–26 s | Vignesh (teasing) | லுங்கி நழுவுனா, கை பெர்மிஷன் கேட்டுட்டா பிடிக்குது? | |
| 26–35 s | Narrator | The verse, then: ஆடை நழுவினா, கை கேக்காமலே பிடிக்கும். அதுதான் நட்பு. | |
| 35–38.5 s | Narrator | உண்மையான நண்பனை, நீ கூப்பிடவே வேண்டாம். | Answer card: கூப்பிடாமலே வருபவன் தான் நண்பன் |
| 38.5–41 s | Narrator | அப்படிப்பட்ட உங்க ஃப்ரெண்ட்-அ டேக் பண்ணுங்க! | |

Why it works: the lungi joke *is* the kural's image (a hand catching a slipping garment without being asked). That makes the story clearly original and lets the verse land as the punchline.

**K1330, "காபி பொடியும் செல்லக் கோபமும்". Kural 1330, adhikaram 133 ஊடலுவகை, காமத்துப்பால். [DONE]**

Verse: ஊடுதல் காமத்திற்கு இன்பம் அதற்கின்பம் / கூடி முயங்கப் பெறின்.

| Time | Who | Line | On screen |
|---|---|---|---|
| 0–3 s | Mithra (sulking) | மூணாவது தடவை மறந்துட்டீங்க! | 9:40 PM / காபி பொடி இல்ல. |
| 3–14 s | Narrator | மித்ரா அதுக்கு மேல ஒரு வார்த்தை பேசல… கதிர் சண்டை போடல. குடை கூட எடுக்கல. மழையில நனைஞ்சுக்கிட்டே, கடைக்குக் கிளம்பிட்டான். | Question card: சின்ன ஊடல்... எப்போ இனிக்கும்? |
| 14–18 s | Narrator | திரும்பி வந்தான். கையில காபி பொடி. தலையில இருந்து சொட்டுற தண்ணி. | |
| 18–22 s | Kathir | மேடம், காபி ரெடி. கோபம் இன்னும் எவ்வளவு நேரம்? | |
| 22–26 s | Mithra (laughing) | ஐயோ... இது காபியா, கஷாயமா? | |
| 26–35 s | Narrator | The verse, then: செல்லக் கோபம் ஒரு இனிமை. அது தீர்ந்து சேர்றது, இன்னும் இனிமை. | |
| 35–38.5 s | Narrator | சண்டை சின்னதா இருக்கட்டும். சமாதானம் சூடா இருக்கட்டும். | Answer card: ஊடலின் இனிமை சமாதானத்தில் தான் |
| 38.5–41 s | Narrator | சண்டைக்கு அப்புறம் காபி போடுற உங்க ஆள டேக் பண்ணுங்க! | |

**K0100, "தீபாவளி கோலமும் அண்ணனின் சொல்லும்". Kural 100, adhikaram 10 இனியவை கூறல். [DONE, posting Wed 4 Nov]**

Verse: இனிய உளவாக இன்னாத கூறல் / கனிஇருப்பக் காய்கவர்ந் தற்று.

| Time | Who | Line | On screen |
|---|---|---|---|
| 0–3 s | Muthu (frowning, no smile) | இதுக்கு பேரு கோலமா? | 6:10 AM / தீபாவளி காலை. |
| 3–7 s | Narrator | ராத்திரி டியூட்டி முடிஞ்சு வந்த முத்து, பார்த்ததும் குறை தான் சொன்னான். | |
| 7–10 s | Muthu | எல்லாம் கோணல் மாணலா இருக்கு. | |
| 10–14 s | Narrator | கயல் கையில இருந்த கோலப்பொடி, அப்படியே நின்னுச்சு. | Question card: முதல்ல கண்ணுக்கு தெரியறது குறையா? |
| 14–17 s | Kayal (hurt, steady) | அண்ணா... இதுல ஒண்ணு கூடவா நல்லா இல்ல? | |
| 17–21 s | Narrator | முத்து மறுபடி பார்த்தான். நடுவுல, அவனுக்கு பிடிச்ச மயில். | |
| 21–24 s | Muthu (soft) | மயில்... ரொம்ப... அழகா இருக்கு, கயல். | |
| 24–33 s | Narrator | The verse, then: பழம் கையில இருக்கும்போது, காயை எதுக்கு பறிக்கணும்? | |
| 33–36.5 s | Narrator | இனிய சொல் இருக்கும்போது, கசப்பான சொல் எதுக்கு? | Answer card: இனிய சொல் இருக்க, கசப்பு எதுக்கு? |
| 36.5–40 s | Narrator | முதல்ல குறை சொல்லுற உங்க அண்ணன், அக்காவை டேக் பண்ணுங்க! | |

**K0301, Thatha and Kavin. Kural 301, adhikaram 31 வெகுளாமை. [DONE, old format]**

Story: Kavin is scolded by the PT sir at school, comes home and takes it out on a puppy, and Thatha asks one question.

Verse: செல்லிடத்துக் காப்பான் சினங்காப்பான் அல்லிடத்துக் / காக்கின்என் காவாக்கா லென்?

| Who | Line |
|---|---|
| Kavin (hook) | போ! போ இங்கிருந்து! |
| Thatha | என்ன, ஸ்கூல்ல யாராவது திட்டினாங்களா? அவங்க கிட்ட ஏன் கத்தல? |
| Kavin | அவர் பி.டி. சார், தாத்தா! அவர் கிட்ட எப்படி? |
| Thatha | இந்தக் குட்டி கிட்ட மட்டும் முடிஞ்சுதா? |
| Thatha (kural) | வள்ளுவர் என்ன சொல்றார் தெரியுமா? …, then the verse |

Lesson card: பலவீனமானவர் மேல் கோபம் காட்டுவது வீரம் அல்ல.

The script ended with a teaser, "பெரியவங்க மேல கோபப்படலாமா? அடுத்த குறள்!" (குறள் #302 ➜). **[SUPERSEDED]** Teasers are banned from 29 Oct. Whether the posted K0301 v17 still contains it is UNKNOWN.

### Rejected or corrected examples, and why

| What | Episode | Why it was changed |
|---|---|---|
| "ஒரு கால்." under 3:04 AM | K0788 | Reads as "one leg". Changed to "ஒரு அழைப்பு." |
| "சேவ் பண்ணுங்க" ending | K0788 | Ananya didn't want a save prompt. Replaced by the narrator's tag-a-friend line. |
| Question and answer cards looking like stray subtitles | K0788 v6 | "it feels something odd". Ananya picked handwritten cards (P3). My pick, the P1 title card, was not chosen. |
| Subtitle style C (two-step) and hook H1 (call banner) | K0788 | These were my recommendations. Ananya chose karaoke A without the strip, and H2 timestamp. |
| Kural card plus blur at 26–28 s | K0301 v14 | Rejected by Ananya. |
| Kural card across the faces | K1330 v2 | Moved up into the rainy sky. |
| The hook line heard again in the loop at 39 s | K0788 v4 | The hook audio must not repeat at the end. |
| Narrator and dialogue subtitles on screen together | K0788 v4 | Confusing. They are now never shown together. |
| Badge "flick" animation | Plan, 28 Oct | Dropped. |
| Cards with 🔔 schedule lines or dates | K0301 | Removed for good. |

---

## D. AI video production

### Tools in use
- **[CONFIRMED] Google Flow** (flow.google.com) makes all images and video clips.
  - Video model: Omni Flash 720p, followed by Flow's free 1080p upscale.
  - Image model: Nano Banana 2 Lite, free in Flow.
  - Clip cost: 4 s = 7 credits, 8 s = 12, 10 s = 15.
  - Plan: Google AI Plus, which Ananya upgraded to (200 credits a month plus 50 a day). Which account that applies to is UNKNOWN.
  - Flow is driven by **flow-mcp**, a local tool in `~/flow-mcp`, using the Chrome profile `~/.flow-mcp/chrome-profile` on debug port 9333. flow-mcp also has its own dashboard at http://127.0.0.1:8787 (`node dist/studio.js`), added 19 Sep 2026 in commit e6d027a under GitHub account GTAI-1. It is separate from Studio Live.
- **[CONFIRMED] Gemini TTS** (`gemini-3.8-flash-tts`) does the voices, on a free AI Studio key (10 requests a day, reset at 12:30 IST). Narrator Charon; each character gets its own voice.
- **[CONFIRMED] FFmpeg** on the Mac does assembly: cuts, two-pass loudnorm to −14 LUFS, freezedetect and mpdecimate checks. Subtitles are drawn with Pillow because libass was unavailable. **whisper.cpp** does transcript checks. `lipsync.py` fits our voice lines onto Flow's speech spans.
- **[CONFIRMED]** Music is our own, made by `tools/make_music.py`: three raga beds (hindolam_calm, mohanam_playful, suddha_dhanyasi_warm), a tanpura, and a closing bansuri (flute) phrase under the logo ending. Music sits at −20 dB and dips while anyone speaks.
- **[CONFIRMED]** Font: Kavivanar (Google Fonts, OFL licence) for the handwritten cards, downloaded with Ananya's OK on 30 Oct into `assets/fonts/`.
- **[CONFIRMED]** `caffeinate` keeps the Mac awake during long runs.

### Tools rejected or not used
- **[SUPERSEDED]** The original plan of Anthropic API, Gemini API and Veo was replaced by the zero-spend setup.
- **[CONFIRMED] ElevenLabs:** rejected, because the free tier forbids commercial use. A config block still exists; do not use it.
- **[CONFIRMED] Google Cloud TTS:** rejected, because it needed a ₹1000 prepayment.
- **[EXPERIMENT] Flow's own voice:** compared with ours on K0301. Ananya preferred Flow's audio but declined to spend credits, so Gemini TTS was used. The pipeline can still use Flow's voice per character (`voice_source: flow`) when the Tamil is clear and consistent.
- **[FUTURE] Tool comparison (26 Oct):**
  - Paid options suggested: Kling Standard (about $7 a month, up to 15 reference images, commercial rights), the Gemini API with Omni Flash (about $1 per 10 s), Higgsfield ($19 a month and up), and Sync lipsync-2 or Hedra for Tamil lip sync.
  - Kling's free tier is personal-use only.
  - Open models (LTX, Wan) are not practical on her 24 GB M4 Pro.
  - No switch was decided; Flow stays.
- **UNKNOWN / not used: OpenArt, InVideo, HeyGen.** None of them appears anywhere in the project record.

### Flow accounts and projects
- **[CONFIRMED]** One Flow project per episode. A "recurring" project for the series cast is planned but not created.

| Episode | Flow project | Account |
|---|---|---|
| K0301 | b7755f8b-6f52-4abf-8563-86ab7a09d09d | first account, orukural.orukadhai1330@gmail.com |
| K0788 | dbd31b05-2737-4682-a9ab-b83a04d7ffdf | new account, /u/2, from 28 Oct |
| K0788 (archived) | 17cdee32-abf4-4416-8c3d-321b921530b4 | old account, /u/1; shot 5 came from here |
| K1330 | c67884f6-487e-43e9-a6c8-e555ed19f88e | new account, /u/2 |
| K0100 | 79afd990-d322-4100-871c-d97938a32a86 | orukural.orukadhai1330, /u/1; Ananya opened this project herself |

- **Credit history:**
  - New account: about 1050, then 993 after K0788, 915 after the K1330 clips, and 891 after the K1330 remakes.
  - orukural.orukadhai1330 account: 153 before K0100, about 80 after.
- **[UNRESOLVED]** The skill and `AGENTS.md` say "use only the new account (the one that owns dbd31b05)", but K0100 was made in the orukural.orukadhai1330 account because Ananya supplied that project. The new account's email address is UNKNOWN. Ask Ananya which account to use for K0467.
- **[CONFIRMED]** Don't automate across several Gmail accounts to stack free credits. It was flagged as an account and terms risk.

### Production workflow for one reel (the order that worked)
1. **Script.** Draft `script.md` and `script.json`, run `studio.py script-check N` (credit cap, cast log, the bare "கால்" warning), and send it to Ananya. Wait for "approved" or "go ahead".
2. **Reference images (free).** Make a character sheet per person, one place plate per location, and one master per recurring object. Make the place image from the object's tile so both match: for example, the house front was made from the top-down peacock kolam.
3. **Shot stills (free).** One still per shot. Reference the project's existing tiles (`asset:<name>`) and never re-upload PNGs: re-uploading made duplicates, and all 7 K1330 jobs failed while the uploads processed. Send a contact sheet to Ananya and wait for her approval.
4. **Clips (credits).** Generate one clip at a time from the approved stills. Check each one, and download it at the 1080p upscale (`download_quality: "upscaled"`). Ask before any paid retry.
5. **Voice (free, 10 a day).** One take per line, words only, then a pitch and transcript check.
6. **Rough cut.** `studio.py assemble`, with lip-sync fitting, karaoke subtitles, cards, music, sound effects and zooms (`edit.json`). Self-review frame by frame, then open it in QuickTime for Ananya.
7. **Fixes.** Try free fixes first (re-timing, re-cutting, moving cards). Offer clip remakes with the credit cost on a decision card.
8. **Final.** `studio.py assemble --final` (CRF 15, slow, AAC 320k), saved as `review/KNNNN/KNNNN_final_1080src.mp4`.
9. **Publish pack.** `studio.py publish-pack N` writes `episodes/KNNNN/publish/KNNNN_post.md` and `KNNNN_cover.jpg`.
10. **Post.** Only on the go-ahead (see section E).

### Real Flow prompts (K0788, accepted)
- **Shot 1, image prompt:** "Saro stands in the open doorway of his house at night, phone pressed to his right ear, eyes wide with panic, free hand gripping the door frame; the doorway bulb behind him, the dark street to the right."
- **Shot 1, motion prompt (start):** "Saro speaks urgently into the phone. After he finishes, a bright white motorbike headlight sweeps across his face from the street: Vignesh (lean, thin black rectangular glasses, short side-parted black hair, blue-and-white checked shirt open over a navy T-shirt, grey track pants) rides his plain dark-grey motorbike in from the r…" (the record cuts it off here).
- **Shot 3, motion prompt:** "Saro lets go of the key; Vignesh closes his hand around it and speaks to Saro, calm and quick; Saro nods. Exactly one key in the whole shot, in Vignesh's hand once Saro lets go; nobody holds anything else."
- **Prop description:** auto_key: "A single auto-rickshaw key on a small brass ring with a red thread tassel." (Tamil name சாவி)
- **Prompt rules:**
  - Image prompts give only the composition. Looks, outfits, place and style come from the cast, the continuity bible and the reference images.
  - Never ask for text, letters or logos in generated media.
  - One simple action and one camera behaviour per clip.
  - Say "exactly one <object>".
  - Write "frowning, no smile" on angry lines.
  - Speakers face the camera so the mouth is visible.
- **[CONFIRMED]** Visual style: "Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field."
- **[CONFIRMED]** At most 3 reference images per Flow image (a flow-mcp limit): characters first, then the place, then props. Anything else is described in words.

### Visual style and on-screen signature
- **[CONFIRMED]** Logo: Ananya's small round badge, at x 825, y 1669, covering Flow's sparkle watermark. It replaced an earlier badge. She chose to keep the badge over the watermark and rely on the AI labels for disclosure.
- **[CONFIRMED]** Kural reveal: clean text, centred, on a frame dimmed to 0.75 (option B). It can be moved per episode (K1330 into the sky; K0100 `text_y: 430`).
- **[CONFIRMED]** Logo ending: 2 s with the flute phrase. This is the only still frame allowed.

### Audio
- **[CONFIRMED]** Voices: 0.15 s gaps between lines. Natural clip sound at −6 dB, muted on shots where someone talks.
- **[CONFIRMED]** From K0100: synthesised, licence-free sound effects, with sources and licences recorded in `episodes/K0100/sfx/LICENSES.md`. The set is a whoosh on the hook card, kolam powder sprinkles, a heartbeat under the question, a chime on the reveal, a diya flicker, and dawn ambience with birds and distant crackers. They are set in `edit.json` (for example `"sfx": [{"file": "sfx/chime.wav", "shot": 5, "at": 1.0, "gain_db": -17}]`) and dip under the voices.
- **[CONFIRMED]** Zooms are set per shot in `edit.json` (for example `"1": {"zoom": {"from": 1.0, "to": 1.08}}`). Keep them subtle: about 1.0 to 1.08.
- **[UNRESOLVED]** `AGENTS.md` and the 28 Oct plan still say "never pan or zoom". Ananya's 31 Oct instruction allows zooms on real clips. Follow her instruction, and treat the old line as banning fake motion on stills only.

### Editing and QC checklist (run before Ananya sees anything)
- Frozen frames: none over 0.3 s, except the logo ending.
- Lip sync: the mouth moves on the line, and any speed change stays within 0.9–1.1×.
- Phone calls: the phone is at the ear, never at the chest.
- Objects: one of each, nothing appearing or vanishing (cups, tumblers, phones, kolams).
- Doors and gates: attached properly, not floating; correct colour.
- Faces, hair and outfits match the character sheet. Watch for hair turning grey, a thinner face, or someone not wet in the rain.
- Nobody smiles on an angry line.
- The action matches the narration (K1330: he must actually leave in the rain).
- Room layout does not shift mid-shot.
- Dialogue lands in time, with no gestures repeated across a cut (the K1330 double arm-fold).
- The hook audio does not repeat in the loop.
- Narrator and dialogue subtitles are never on screen together.
- Text is clear of faces, the logo and the kural.
- Whisper transcript matches the script. Loudness −14 LUFS. Length 35–45 s.

---

## E. Publishing

### How posting works (manual-assisted, in the browser)
- **[CONFIRMED]** Claude posts through the **built-in browser pane of the Claude desktop app** on Ananya's Mac (press Cmd+Shift+B to show it). The browser cannot attach local files, so **Ananya makes four file picks**, and Claude fills in everything else:
  1. Ananya signs in to the Google account that owns the channel and to Instagram orukural.orukadhai, then replies "signed in".
  2. Claude checks that the episode isn't already posted on either platform.
  3. YouTube Studio upload: Ananya picks the video and replies "picked". Claude fills in the title, description, tags, "Not made for kids" and "Altered content: Yes".
  4. Ananya picks the thumbnail (`KNNNN_cover.jpg`) and replies "thumb". Claude sets Public and publishes.
  5. Instagram Create: Ananya picks the video and replies "ig picked". Claude keeps the Original 9:16 crop with sound on.
  6. Ananya picks the cover and replies "cover". Claude pastes the caption, switches the AI label ON, and clicks Share once.
  7. Claude sends back both live links and records them in project memory.
- **[CONFIRMED]** Finder is opened with the right file already selected before each pick.
- **[FUTURE]** Fully hands-off posting through the official YouTube and Meta APIs. It needs a one-time developer setup, and Instagram needs the video at a public URL. Not built.

### YouTube settings
- **[CONFIRMED]** Public. Not made for kids (keeps comments on). Altered or synthetic content = Yes. The custom thumbnail is uploaded before Publish.
- **[CONFIRMED]** Title format: `குறள் <N> | <Tamil curiosity line> | Thirukkural Story #Shorts`, at most 100 characters. Search words matter, because K0301's YouTube views came 53.8% from search.
- **[CONFIRMED]** Description: 2–3 hook lines, a tag line, 📜 the verse, 💡 the Tamil and English meanings, 📖 the adhikaram and paal, the hashtags, then the AI disclosure line.
- **[CONFIRMED]** Tags: Tamil and English, including the kural number, adhikaram, verse words and theme words.
- **[UNRESOLVED]** Pinned comment: the comment was posted on K0788 but could not be pinned. YouTube asks for one-time channel verification (a 6-second video, an ID, or about 2 months of history), and only Ananya can do it. K1330's pinned comment was not posted ("say post comment"). The verification status is UNKNOWN.

### Instagram settings
- **[CONFIRMED]** Cover = `KNNNN_cover.jpg`. Original 9:16 crop. "Add AI label" ON before Share. Share to Facebook off.
- **[CONFIRMED]** Caption: a short hook with an emoji, a 2-line story teaser, 📜 the verse, the tag line with 👇, then the hashtags. No 🔔 line, no dates.
- **[UNKNOWN]** K0301 was shared without the AI label, which can only be added afterwards in the phone app (⋯ → Edit → Add AI label). Whether Ananya did this is UNKNOWN.

### Hashtags
- **[CONFIRMED]** 3–5 in total. The fixed set is `#திருக்குறள் #thirukkural #ஒருகுறள்ஒருகதை`, plus one theme tag (`#நட்பு`, `#காதல்`, `#கோபம்`) and `#tamilstories` on Instagram.

### Covers and thumbnails
- **[CONFIRMED]** A 1080×1920 frame from the reel with Tamil text in the upper part, kept clear of faces so it survives the Instagram grid crop. Made by `episodes/KNNNN/publish/cover.py`. No fake or generated text.
- **[DONE]** Covers so far:
  - K0301: the opening shot with "குறள் #301 · உன் கோபம் யார் மேல்?"
  - K1330: the rainy balcony with "குறள் 1330" and "காபி பொடியும் செல்லக் கோபமும்"
  - K0100: colouring the peacock kolam with "இதுக்கு பேரு கோலமா?"

### Real publish pack: K0788 (as posted)
- **YouTube title:** குறள் 788 | 3 மணிக்கு வந்த நண்பன் | Thirukkural Story #Shorts
- **Description opening:** ராத்திரி 3 மணிக்கு சரோவோட அப்பாவுக்கு மூச்சு விட முடியல. அவன் phone-ல பேசி முடிக்கும் முன்னே, விக்னேஷ் கேட்டுல நின்னான். / உங்க 3 AM நண்பனை tag பண்ணுங்க 👇
- **Instagram caption opening:** ராத்திரி 3 மணி. ஒரு call. 📞 / சரோ பேசி முடிக்கும் முன்னே, விக்னேஷ் கேட்டுல நின்னான். ஆட்டோ ஓட்டினான், பணம் கட்டினான், ஒண்ணும் கேக்கல. 🤝
- **Pinned comment:** உங்க 3 AM நண்பனை tag பண்ணுங்க 👇
- **Tags:** திருக்குறள், thirukkural, thirukkural story, kural 788, நட்பு, friendship, உடுக்கை இழந்தவன், இடுக்கண் களைவதாம் நட்பு, best friend, friends, tamil friendship story, tamil shorts

### Published links
| Episode | Posted | YouTube | Instagram |
|---|---|---|---|
| Kural #001 (before the pipeline, 1:31 long) | before 25 Oct | video UYXNB77JGdQ | UNKNOWN link |
| K0301 | 27 Oct 2026, about 4:55 pm IST | https://youtube.com/shorts/ZYqsCislNog | https://www.instagram.com/orukural.orukadhai/reel/De_wlASJEre/ |
| K0788 | 30 Oct 2026, about 4:25 pm IST | https://youtube.com/shorts/F6HmVInNjME | https://www.instagram.com/orukural.orukadhai/reel/DfHaowDJI97/ |
| K1330 | 2 Nov 2026, about 1:30 pm IST | https://youtube.com/shorts/MxeAbBQPX3E | https://www.instagram.com/reel/DfO07Obp9o_/ |
| K0100 | planned Wed 4 Nov 2026, 7 pm IST, with a reminder at 6 pm | not yet | not yet |

### Analytics (what is known)
- **Kural #001** (25 Oct baseline): 123 Instagram views, 106 reached, 11 likes, 9.9 s average watch, about 45% swiped away in 3 s. 6 YouTube views.
- **K0301** (28 Oct, about 18 hours after posting):
  - Instagram: 1,356 views, about 1,196 reached, 58.6% stayed past 3 s, 12.7 s average watch, 27 likes, 0 comments, saves or shares.
  - YouTube: 13 views, 81.8% stayed to watch, 53.8% of views from search and 0% from the Shorts feed.
  - Later: Instagram about 1,370 views; YouTube 16 views in 3 days.
- **K0788** (about 20 minutes after posting): YouTube 210 views, 4 likes, +1 subscriber (4 in total), 95% from the Shorts feed. Instagram 1 view.
- **K1330:** no analytics in the record. UNKNOWN.
- **[DONE]** Analytics come from Windsor.ai (a trial plan; the data stops if the trial ends) and from reading YouTube Studio and Instagram in the signed-in browser. The report is `reports/K0301-analysis-2026-10-28.md`.
- **[UNKNOWN]** A weekly report was set for Mondays just before 11 am IST, starting 2 Nov. Whether the 2 Nov report ran is UNKNOWN.

---

## F. Automation

- **[DONE]** The `orukural-studio` pipeline (Python, `studio.py` CLI). Commands: `script`, `script-check`, `flow-sheet`, `continuity-sheet`, `visuals`, `voice`, `voice-ab`, `assemble`, `assemble --final` / `render`, `publish-pack`, `approve`, `live`, `flow-progress`, `flow-project`, `event`, `status`, `data build`. It has pytest tests, and they must pass before pipeline changes are committed.
- **[DONE]** Layout:
  - `episodes/KNNNN/` holds one episode: `script.json`, `script.md`, `edit.json`, `lipsync.json`, `visuals.json`, `continuity_review.json`, and the folders `refs/`, `images/`, `clips/`, `voice/`, `sfx/`, `render/`, `publish/`.
  - `review/` holds the cuts for Ananya.
  - `data/` holds the verses, characters, cast log, themes, lessons and pronunciation fixes.
  - `assets/` holds fonts, music, brand, characters and locations.
  - `logs/` holds `events.jsonl` and `spend.jsonl`.
  - `config.yaml` has the settings; `.env` has the secrets (never read or copy them).
- **[DONE]** **Studio Live** dashboard: run `python studio.py live` and open http://127.0.0.1:8765. It refreshes itself every 2 s and shows stages, the shot board, Flow credits (per video, per day, per month), the TTS quota and its reset, failures and retries, and the posting calendar. Built 25 Oct.
- **[DONE]** Flow is automated with flow-mcp, driven by a Claude session on the Mac through Remote Control.
- **[DONE]** Skills in the repo: `.claude/skills/kural-reel/SKILL.md` (the full workflow; the repo copy is newer than the shared one, with the reference-tiles, one-master and download-check lessons) and `.claude/skills/continuity-review/`.
- **[DONE]** Git: branch `plan-3-a-week`. The latest commit is a1dd722 (per-shot zoom and sound effects).
- **[UNRESOLVED]** No off-machine backup. The only git remote is a local `.bundle` file. A private GitHub repo was suggested on 1 Nov, and Ananya hasn't decided. Uncommitted work exists (assets, `plan/`, data edits).
- **[DONE]** On 2 Nov Ananya moved the project from `~/Documents/orukural-studio` to `/Users/ananya-24962/AI/Claude/orukural-studio`.
- **[FUTURE]** Automated posting through the APIs, and weekly analytics rewriting the "From analytics" section of `lessons_learned.md`.

---

## G. Lessons learned (with evidence)

**Story and growth**
- A tense or question hook at frame one beats a slow opening: 45% swiped away on #001, while 82% (YouTube) and 59% (Instagram) stayed on K0301. **[CONFIRMED]**
- 35–45 s works far better than 1:31. **[CONFIRMED]**
- Viewers leave at about 12.7 s, so show the lesson teaser by 10–12 s. **[CONFIRMED]**
- Relationship stories with a tag-someone ending suit a 25–34 audience better than a grandfather story. **[CONFIRMED]**
- K0301 got 0 saves, shares and comments. **[EXPERIMENT]** The tag-line ending (from K0788) is meant to fix that. Its result is UNKNOWN.

**Flow**
- Reference existing tiles and never re-upload PNGs: re-uploads made duplicates and failed jobs (K1330).
- The frame picker lists only about 10–15 recent images and can search the wrong tab (Uploads instead of Images). Search by name, or give the approved still directly as the start frame.
- Large flat props can be drawn twice, overlapping (two kolams in K0100 shot 2). Say "exactly one", and make every image from one master.
- A reference image controls the prop's look (the loose brown door in K0788).
- Flow sometimes closes a door the character should walk through (K1330 shot 3, failing twice for 14 credits). Use a start frame where the character is already stepping out.
- Flow can slip in a second tumbler or cup. Cut before it happens or regenerate.
- Flow refusals and upload timeouts are free. Evenings can be slow (2–3 minutes per clip, with refusals).
- An "unusual activity" warning appeared once. Continue one clip at a time.
- Flow blocks adult-to-child aggression shots.
- flow-mcp once saved an older tile under a shot's name. Check each download is the right shot.

**Voice and sync**
- A delivery note in the TTS text gets read aloud in English (the K0788 bug), and the model refuses system instructions (`400 'Developer instruction is not enabled for this model'`). Send words only.
- Once all speakers got the default voice (K0301 bug). Check each speaker's voice.
- When Flow's mouth movement is longer than our line (K0100: mouth 3.4 s, voice 2.2 s), re-timing can't fix it. A slower take shaped by punctuation can (0.98–0.99× fit).
- A voice stretched by 1.25× sounds rushed. Prefer a new take.

**Review**
- Ananya spots flaws my checks missed (two phones, a floating gate, the phone at the chest, a frozen frame, a vanishing tumbler, a double arm-fold, smiling while scolding). Self-review must be frame by frame before every cut.
- Long renders (10–15 minutes) went silent and looked like hangs. Run renders in the background and post progress every 2 minutes.
- A Claude usage limit paused work for about an hour once (30 Oct). Explain it and resume.

**Publishing**
- Switch the Instagram AI label on before Share; the web can't add it afterwards.
- Upload the YouTube thumbnail before Publish.
- A "?" makes a request a question. Confirm before an irreversible step.

---

## H. Status (as of 2 Nov 2026)

**Done and published**
- K0301 (27 Oct): v17 final, after 17 drafts and 97 credits. Ananya: "BRO FINALLY 17TH VERSION IS FINEE."
- K0788 (30 Oct).
- K1330 (2 Nov).

**Ready, waiting to post**
- **K0100**, Wed 4 Nov at 7 pm IST, with a reminder at 6 pm.
  - Final: `review/K0100/K0100_final_1080src.mp4`
  - Pack: `episodes/K0100/publish/`, title "குறள் 100 | தீபாவளி கோலமும் அண்ணனின் சொல்லும் | Thirukkural Story #Shorts"

**Next**
- **[FUTURE]** K0467 (office), then 785, 1100, 190, 104.
- **[UNRESOLVED]** Which Flow account to use for K0467.

**Open items**
- **[UNRESOLVED]**
  - Repo backup (private GitHub?), archiving old drafts, and replacing the stale copies in the shared folder.
  - Pinned YouTube comments (channel verification).
  - The K0788 shot 5 1080p swap (the clip is in the old account).
  - The K0301 Instagram AI label (phone app).
- **[UNKNOWN]** Whether the Monday weekly report ran on 2 Nov, and analytics for K0788 after day one and for K1330.
- **[UNRESOLVED]** `data/lessons_learned.md` still says "End on a short lesson card with 'Save this'". That contradicts the later decision of no save text. Ask before editing it.

**Roadmap ideas [FUTURE]**
- A monthly kids' special with Thatha and Kavin.
- Thatha video-call cameos.
- Adhikaram compilations of 8–10 minutes.
- An Instagram Story poll the same evening as each post.
- Replying to every comment in the first hour.
- API auto-posting.
- Possibly Kling for character shots, if spending is ever allowed.

---

## I. How to work with Ananya

**Communication**
- Short messages, often in Tanglish (for example "mayil romba azhaga iruku kayal dialogue and video sync is not same"). She calls Claude "bro".
- "?", "??", "update" and "is it done" mean she has waited too long. Answer at once with the exact state.
- Give progress every 2–3 minutes during long work. Lead with the answer.
- Give her file paths and open the files for her (QuickTime for videos, Preview or Finder for images and contact sheets).
- Use decision cards for choices, with one recommendation. She often picks quickly ("hook 2 is nice", "i feel handrwritten is fine").

**Her review style**
- She watches every cut and reports exact seconds ("16, 42nd seconds…", "in 4th second, mithra folds her hand 2 times").
- She expects Claude to catch continuity and sync flaws first, and gets frustrated when she has to point out repeated mistakes.
- When she asks for "15 flaws" or to "find flaws", do a real frame-by-frame pass and list them with timestamps.

**Money and credits**
- She is careful with credits and prefers free fixes. Always state the credit cost before spending.
- She knows the free paths (the Flow upscale is free; voices reset daily) and expects them to be used.

**Approvals she has given and how**
- "approved", "go ahead", "post now" and option cards.
- Approval covers that step only. Do not carry it to the next episode.

**Boundaries**
- No passwords in chat.
- Don't touch the Documents folder.
- Don't delete, rearrange or overwrite files without her OK.
- Don't edit flow-mcp without asking.
- Don't use other Gmail accounts for credits.

**Tone**
- Plain, friendly, specific. Apologise briefly when something went silent or went wrong, then fix it.

---

## What I could not access or chose not to include

- **`~/Documents`:** not accessed, by Ananya's rule. Older drafts there (for example `K0301_final_v17.mp4`, loose screenshots) were not re-checked.
- **The money channel thread ("Continue money channel Episode 1"):** excluded on purpose.
- **`.env`:** not read, because it holds secrets.
- **Artifacts not re-read in full:** the "4 reels a week plan" (the repo copy was read only in part), the K0301 first-run review, and the dashboard concept mock-ups. Their comment threads are summarised from the chat, not quoted.
- **Not available anywhere:** Instagram app-only insights (retention graph, traffic sources), YouTube retention curves, any analytics after 30 Oct, and how Kural #001 was made.
- **Truncated in the source:** full shot lists and every Flow prompt for all episodes. Only examples are included here; the complete prompts are in each `episodes/KNNNN/script.json`.
- **Not in the record at all:** OpenArt, InVideo and HeyGen.

---

## K0467 production log (4 Nov 2026)

- **[CONFIRMED] Flow project:** https://flow.google.com/project/0e34f70e-be49-4bb0-b336-c4100d2dee30 (the old `89e57707…` link in config.yaml no longer exists; config.yaml and flow/README.md were updated). Account: orukural.orukadhai1330 (132 credits at the start).
- **Made:** 9 reference images, 9 shot images, 9 Omni Flash 720p clips (93 credits; 39 left). Ananya first capped the spend at 75, then approved shots 7 and 8 (24 credits) after seeing the first 7 clips.
- **Fixed before clips:** shot 2 and shot 8 had Ravi outside the glass wall; both were regenerated with "INSIDE the room" and the old versions were deleted at her request. In the shot 1 line, a stray Bengali letter in "செய்ய" was corrected.
- **Mistake to avoid:** I downloaded the 720p original first, which breaks rule 6. The 720p files are kept in `episodes/K0467/clips/720p_first_download/`; the 1080×1920 upscales are now `clips/shot01–09.mp4`. Always choose "1080p Upscaled" in the download menu first.
- **Flow upscale behaviour:** one upscale at a time. A 4 s clip takes about 1 min and an 8 s clip about 2 min. Leaving the page cancels it, so wait on the clip page until the file lands in `~/Downloads`, with the title in the file name.
- **Download order in the Videos grid** is newest first (8, 7, 6, 5, 4, 2, 9, 3, 1). File names carry the clip title, so map them by name, not position.
- **Picking frames and references in Flow:** type the asset name in the picker search (it works when the field is focused). The unfiltered list reorders after every generation, so never click by row position.
- **Prompt gap found by Ananya:** shots 7 and 8 were written with "no speech", so Flow made silent clips and there is nothing to lip-sync. Spoken Tamil lines must be in the clip prompt, in quotes, whenever Flow's voice may be used.
- **Audio workarounds agreed:** shot 1 ("நாலணா மணி" is not clear in Flow audio) and shot 2 (Ravi says "சீனியர் டெவலப்பர் ராவி வந்து சொல்றான்" about himself) use the Gemini narration instead of Flow's audio. Shot 6 (Ravi walking in) is cut in the edit. Nothing is regenerated.
- **Stills:** `episodes/K0467/images/shot01–09.png` are first frames cut from the 1080p clips (the pipeline needs an image per shot), not the original Flow stills.
- **Draft v1 is blocked by the voice:** `studio.py assemble 467` refuses to render. The Gemini voice files are much slower than the script allows: line 1 is 8.2 s for about 3.9 s of text, line 3 is 10.2 s for 6.0 s, line 6 is 14.6 s for 9.0 s, and line 8 is 4.3 s for 2.2 s. They need to be remade (`studio.py voice 467 --force`, free) with a faster pace, or Flow's own voices used with lip sync. Waiting for Ananya's choice.

**K0467 update, 4 Nov (later):**
- **Voice model:** only `gemini-3.8-flash-tts` speaks (free tier: 10 requests a day, 3 a minute, reset at midnight Pacific = 1:30 PM IST). "Gemini 3.6 Flash" is a text model and returns 404 for TTS. Config is unchanged.
- **Script fixes:** line 1 is now "நாலு மணிக்குள்ள backend system முடியணும். எந்த solution-னு தெரியல." (Ananya's wording; "naalana" removed). A stray Bengali letter in line 1 was removed. The "அடுத்த குறள்!" teaser was cut from line 8 (no next-kural teaser rule). Backup: `script.json.bak`. Old slow voice files: `voice_v0_slow/`.
- **Lesson:** a bad character inside Tamil text makes Gemini read the line about twice as slowly. Check for non-Tamil characters before blaming the model.
- **Draft v1 status:** voice now fits. `continuity_review.json` is marked pass on Ananya's say-so (she reviewed in Flow). `assemble 467` stops because the picture would freeze: shot 1 (0.9 s), shot 3 (2.4 s) and shot 6 (about 1.5 s at the end), where the clip is shorter than its shot. Needs a retime of those shots or a slow-down of no more than 0.85x.

**K0467 draft v1 (4 Nov, evening):** built as `episodes/K0467/render/K0467_draft.mp4`, 48.9 s (above the 35–45 s target). Script lines 2–8 were trimmed and rewritten in natural spoken Tamil (backup `script.json.before_trim`), voice remade on a second free Gemini key (the first hit 10 requests a day; the limit is a rolling window, not a midnight reset). Line 1 had 0.25 s of leading silence trimmed by hand (`seg01_hook.before_trim.mp3`) and the voice.json seconds edited, so do not re-run `studio.py voice 467` before assembling or it restores the untrimmed file. Open flags: shot 2 voice is slowed to 0.80x to follow Flow's mouth, line 2 starts before line 1 ends, and line 8's narrator pitch was measured at about 200 Hz (outside the narrator range).

**K0467 draft v2 (4 Nov, later):** Ananya rejected v1's lip sync (audio and subtitles fine) and asked for every clip to be regenerated against the final audio in a **new Flow project on a different account**: https://flow.google.com/u/2/project/9e4978f5-18f7-474a-8188-9f53b2b5435e (Revathi Satheesh, 838 credits at the start; /u/2). Flow's upload did not work through browser control (even a 10 KB test image only showed "Processing"), so the references and 9 shot images were regenerated there (free). Script shots and segments were retimed to the final voice (`script.json.before_retime` is the backup); each clip prompt now carries the exact line it must speak, with one line per shot (1 to 4 and 6 to 8 speak; 5 and 9 are silent). Clips: 5 of 6 s and 4 of 4 s, downloaded at 1080p (`clips/`; the first set is in `clips_v1_oldflow/`). Draft: `episodes/K0467/render/K0467_draft_v2.mp4` (35.5 s). Known: the lip-sync step still speeds or slows the voice in shots 4 and 7 (about 1.25x and 0.8x), and line 7 starts before line 6 ends.
**Method notes:** the Start-frame and reference pickers work by typing the asset name into the search field; clips download via the editor page at the "1080p Upscaled" item and must stay on that page about 1 minute (4 s clip) or 2 minutes (6 to 8 s clip).

**K0467 draft v3 (4 Nov, evening):** fixed three review notes from Ananya. (1) Title card is now "நாலு / மணிக்குள்ள முடிக்கணும்!"; the odd cards at 19 s and 30 s were reworded and the "குறள் #468 ➜" teaser card removed. (2) and (3): `orukural/assemble.py` `real_timeline()` now keeps a deliberate silent gap of more than 0.3 s between script segments (a silent shot, or a pause before a line) as real time; before, the gap was squeezed away by the planned-to-real remap, so a silent shot shrank and the next line played about 1 s before its shot appeared. K0467 uses it: the silent shot 5 keeps 3 s, and a 0.7 s pause sits between lines 6 and 7. Backup: `scratchpad/assemble.py.orig`; 67 tests pass. Draft: `episodes/K0467/render/K0467_draft_v3.mp4` (39.4 s). Script backups: `script.json.before_gapfix`, `.before_fix3`, `.failed_attempt`.
**Reminder for new scripts:** to get a silent beat or pause, leave a gap in the script between one segment's end_s and the next one's start_s; shots must span the same gap.

**K0467 published (4 Nov 2026):** final render `render/K0467_final.mp4` (CRF 15, 39.4 s), cover `publish/K0467_cover.jpg`, text in `publish/K0467_post.md`. YouTube Short https://youtube.com/shorts/F2VpdIn3fbI (Public, not made for kids, AI use Yes, cover as thumbnail); Instagram reel https://www.instagram.com/orukural.orukadhai/reel/DfUNs-ppBGm/ (AI label on, cover set). Instagram got a 9 MB two-pass copy of the final (the upload tool limit is 10 MB). Pinned comment not posted yet. Cover text must be rendered with `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.
