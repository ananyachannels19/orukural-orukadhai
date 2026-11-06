# K0785 retro: நாலு வருஷம் பேசாத தோழி (The friend who hadn't called in four years)

- Kural / adhikaram / bond: #785 புணர்ச்சி பழகுதல் வேண்டா (79 நட்பு, Friendship) / friends (Selvi, Janani, cousin Pavi). Draft and final approved 6 Nov 2026.
- Flow account and project: Revathi Satheesh (`revathisatheesh2604@gmail.com`), project `9301339c-7e97-4836-b6f3-7bf24bc2ef12` ("K0785 – Friend who did not call"). All work done in Chrome with the Claude in Chrome tools; the `flow` MCP window was never used for this episode.
- Credits: planned 74 / used 98 (remakes: shot 2, 12 cr, Pavi in profile with a closed mouth during her line; shot 4, 12 cr, Janani and Selvi swapped places mid-clip). Over the 75 cap with Ananya's explicit approval. Voice: 14 Gemini TTS requests over both keys.
- Hook type used and where viewers dropped (when analytics exist): tense_moment ("நாலு வருஷம் போன் இல்ல. வருவாளா?"). No analytics yet.

## Prompts that worked
- Shot 5 (Selvi, tearful, the single round tiffin): one person, face to camera, one object held close, the exact line in quotes. Mouth moved for the whole line; no redo.
- Shot 3 (Selvi puts the phone down, then speaks): "first three seconds nobody speaks, then she turns to camera and says her line". Lines landed where the prompt said.
- Shot 4 redo: "Janani is already standing in front of the counter ... does NOT walk ... Selvi and Janani never swap places". Naming what must not move stopped the swap.
- Closed, single tiffin with its lid on ("No other pots or boxes on the counter") fixed the split lid and body in shot 6.

## Prompts that failed, and the fix
- Shot 2 (first try): the start image had Pavi in profile, so Flow animated the line over a closed mouth. Fix: new start image with her face turned to camera, "lips and jaw clearly moving".
- Shot 4 (first try): "Janani walks up from the road" made her walk round the counter and swap places with Selvi. Fix: start already in position and say she stays.
- Image stage: Flow drew a stacked two-tier tiffin carrier (shots 5 to 7) and split the tiffin into a lid and a pot (shot 6). Fix: "single box, closed, not a stacked carrier", and a prop reference that matches.
- Shot 1 image first came out too wide for a lip-synced hook and with an older-looking Selvi. Fix: "tight medium shot, waist-up" and "young-looking 28-year-old, not middle-aged".
- Selvi's first character sheet read as a teenager. Fix: "clearly adult, mature face, fuller figure".

## Ananya's review notes
- Draft, about 40 s: "Pavi speaks something before the end card, that can be removed." Did I catch it first? No. I flagged faint speech in shot 7's Flow audio in my own notes but cleared it after listening only to the mix at the wrong window. New QC check: for every clip, run speech detection on its own sound (`lipsync._flow_parts`) and transcribe the last 3 s of the draft; if a narrator-only shot has speech, mute it. Fixed by muting 5.2 s to the end of the shot 7 clip sound (original kept).

## Voice and sync issues
- 11 lines, 10 free requests a day on one key: lines 10 and 11 and retakes used `GEMINI_API_KEY_2` after Ananya said to.
- The hook line ran 4.2 s whatever the delivery note said, so it did not fit a 3 s slot and a 4 s clip (79 credits). Trimmed wording (approved) to "நாலு வருஷம் போன் இல்ல. வருவாளா?".
- Flow's mouth is shorter than our line: line 3 needed 1.18× and the hook phrase 1.25× (capped). Others 0.93× to 1.15×. A faster retake of line 3 helped. Delivery notes barely change Tamil pace; wording length does.
- The narrator's line 2 measured 208 Hz (expected 70 to 175 Hz); Ananya listened and said it is fine.
- Cache key ignores the delivery note, so changing delivery needs `--force` to retake.

## Process mistakes (time or credits lost)
- 24 credits on two clips I could have caught at the image stage: a profile face on a speaking shot (shot 2) and a prompt that told a character to walk (shot 4).
- Assemble stops without `voice/voice.json` (written only by a full `studio.py voice N`) and `visuals.json` (`studio.py visuals N`), when voice lines were made one at a time. Run both before the first assemble.
- Stray text from a skipped picker click landed in the Flow prompt box twice, and one click hit a heart icon and turned on a Favorites filter. Click the "+" only after the composer is empty and wait 2 s after opening a picker.
- The venv has no Raqm text shaping, so Pillow draws pre-base Tamil vowel signs wrongly on the cover ("போன்" splits). Use wording without ெ ே ை ொ ோ ௌ for cover text, or install libraqm.

## Analytics
(~20 min, next day, later) Not posted yet.

## Proposed lessons for data/lessons_learned.md
(only if repeated in 2+ episodes or Ananya confirmed; she approves the edit)
- Not yet repeated across episodes, so nothing is proposed now. Candidates to watch: (1) a speaking character must face the camera in the start image or the mouth stays closed (K0785 shot 2); (2) never tell a speaking character to walk round furniture, state where they stand and that they stay (K0785 shot 4); (3) a stray voice in a narrator-only clip is audible in the mix and needs muting (K0785 shot 7).
