# Reference for orukural-orukadhai

Read the section for the stage you are in.

## Script details

- Beat map: 0–3 s hook, 3–25 s story (question card at 10–12 s), 25–35 s kural (narrator, slow), 35–43 s lesson card then the tag line.
- One specific, surprising, emotionally true situation about a real bond, today in Tamil Nadu. One person errs; the wiser one asks a question; the realisation is the other's. Never a retold folk tale.
- The kural image should be the story's image (K0788: a hand catching a slipping lungi).
- Meanings are the channel's own words. Do not copy any published commentary.
- Dialogue: natural spoken Tamil for the relationship; each character keeps one form of address all episode. Ending tag lines split evenly over two lines.
- At most one child (4–15) and one elder (50–80), only if the story needs them. Thatha and Kavin only for a kids' special or an explicit video-call cameo (`thatha_cameo: true`).
- Illness shown calmly. No real people, brands, politics, religious conflict.
- Style: "Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field." Palette: terracotta, turmeric, neem green, temple-lamp gold, indigo night.

## Flow prompt rules

- Image prompts give composition only; looks, outfit, place and style come from the cast, continuity bible and reference images. Reference images steer more than prose: fix the reference, not just the prompt.
- Clip prompt: one simple action, one explicit camera behaviour, the exact spoken line in quotes, speaker facing camera with mouth visible, "exactly one <object>", "frowning, no smile" on angry lines, nothing about text or logos.
- Keep a person fully INSIDE a room/glass wall by saying so. Use a start frame already in motion if Flow keeps closing a door the character must pass.
- Silent shots are fine, but only if there is no line to sync; otherwise the line must be in the prompt.
- Frame pickers: type the asset name in the search field; never click by row position (the list reorders). Check the Images tab, not Uploads.
- Downloads: one upscale at a time; a 4 s clip takes about 1 min, 8 s about 2 min. Stay on the clip page until the file lands in `~/Downloads`. Map files by title, not position (grid is newest first).
- If an "unusual activity" warning appears, continue one clip at a time.

## Voice and sync

- Narrator Charon; each character a distinct Gemini voice matched to gender and age (`data/characters.yaml`).
- Check pitch per line, whisper transcript against the script, and non-Tamil characters before blaming the model.
- If Flow's mouth runs longer than our line, re-timing cannot fix it: make a slower take shaped by punctuation. A stretch above 1.1× sounds rushed; prefer a new take.
- Lines must land on their action. Small breaths can push lines late.
- Keep the hook audio from repeating in the loop. Narrator and dialogue subtitles never on screen together.

## QC checklist for every cut (before Ananya sees it)

- No frozen frame over 0.3 s except the logo ending (`freezedetect`, `mpdecimate`).
- Mouth moves on each line; no silent mouth movement; no line over a closed mouth.
- Phone at the ear on calls. One of each object; nothing appears or vanishes (cups, tumblers, phones, kolams).
- Doors and gates attached and correct colour. Faces, hair, outfits match the sheet (watch hair greying, thinner faces, dry people in rain).
- Nobody smiles on an angry line. Action matches the narration. Room layout steady. No repeated gesture across a cut.
- Text clear of faces, logo and the kural. Subtitles never over the kural.
- Whisper transcript matches the script. Loudness -14 LUFS, true peak -1 dBTP. Length 35–45 s.
- Final: 1080x1920, 30 fps, H.264 CRF 15 slow, AAC 320k.

## Credits log

Per episode in `episode.yaml`: planned, used, remakes with reason. Flow price: 4 s = 7, 8 s = 12, 10 s = 15 credits.

## Style defaults (chosen on K0788, keep consistent)

- Hook card H2: a typed timestamp such as "3:04 AM" with a short second line; it must not look like a subtitle.
- Karaoke subtitles for dialogue: white, the spoken word lit yellow (#FFD54A), outline and shadow only, no grey strip. Noto Sans Tamil ExtraBold, size 52, 400 px above the bottom edge. Narrator subtitles in soft yellow italic (#FFE08A).
- Question and answer cards handwritten in Kavivanar (`assets/fonts/Kavivanar-Regular.ttf`).
- Kural shown as clean centred text on a frame dimmed to 0.75; position can move per episode in `edit.json` (`text_y`).
- Small round channel logo over Flow's watermark; 2 s logo ending with the flute phrase (the only allowed still frame).
- Music: own raga beds from `tools/make_music.py`, about -20 dB, dipping under voices. Sound effects and ambience are synthesised, licence-clear, set in `edit.json`; zooms per shot in `edit.json` (about 1.0 to 1.08).
- Final render: `python studio.py assemble N --final`, output `review/KNNNN/KNNNN_final_1080src.mp4`; keep the previous final as `_v1` before overwriting.
