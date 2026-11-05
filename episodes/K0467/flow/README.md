# Flow jobs for K0467

Make each item in Google Flow and save it to `save_as` (paths are relative to the repo). Use this episode's own Flow project, "K0467 – The cost of changing your mind": https://flow.google.com/project/89e57707-dd73-439e-bb3d-47d5f53883ee

**Never generate the same thing twice.** Every job has a `flow_name`. Before generating, search the Flow project for an asset with that name (or the same prompt); if it exists, download it to `save_as` instead. Name each new generation with its `flow_name`. If Flow or the tool reports an error or timeout, look in the project first: Flow often finishes jobs that were reported as failed. Only then retry.

**Never wait idle.** While a job runs, check the Flow page every 30-60 s. A failed tile, or no progress after 2 min (image) or 4 min (clip), counts as a failure: look for a finished result, then retry up to 2 times. Post a one-line note after each finished clip. If Flow shows "unusual activity", stop and tell the user; never try to get around it.

**Clip frames come from the project.** For a clip's start (and any end) frame, pick the existing image tile in the Flow project (search or scroll the picker by flow name). Upload or generate only if it is truly missing, and then only once. **Delete failed tiles** (failed generations with no usable result); never delete a successful image or clip without the user's say-so.

**Log every job for the live dashboard:** `python studio.py event 467 <stage> <status> --shot N --attempt K --credits C --credits-left L --detail "..."`, with stage refs/images/image_check/clips/clip_check and status start/done/fail/retry/blocked. Log credits_left from Flow after every clip.

Work in this order:

1. **References** (characters, places, props). The episode's own cast and places are made for this episode (`refs/`); series ones are made once and reused.
2. **Shot images**, attaching every listed reference image in the listed order.
3. **Image review.** Run `python studio.py continuity-sheet 467` and follow the continuity-review skill (`.claude/skills/continuity-review/SKILL.md`): compare every image with the references, redo any that drift (images are free), and mark each one `pass` in `episodes/K0467/continuity_review.json`. Do not start clips until every image passes; clips cost credits.
4. **Clips**, from the reviewed images. They need 93 credits over 1 day(s): 1050 daily credits a day. Spend daily credits before monthly ones. Make only today's day number; if credits run out, stop and continue after the reset. Never buy credits.
5. **Clip review.** Run `continuity-sheet 467` again, check the first, middle and last frames of each clip, and mark clips `pass`. Redo a drifting clip only if credits allow; otherwise note it and tell the user.
6. Run `python studio.py visuals 467`, then `render 467`.

## Character reference: priya → `episodes/K0467/refs/characters/priya.png`

Flow name: `ref_character_priya`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Priya, a 26-year-old Tamil backend developer. Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. White shirt with loose black blazer, dark trousers, silver earrings. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Character reference: ravi → `episodes/K0467/refs/characters/ravi.png`

Flow name: `ref_character_ravi`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Ravi, a 32-year-old Tamil senior software developer. Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Light grey polo shirt, dark jeans, simple black watch. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: office_cubicle → `episodes/K0467/refs/locations/office_cubicle.png`

Flow name: `ref_location_office_cubicle`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. A tech company's open-plan office with modular desks. Cool fluorescent overhead lights mixed with warm window light; soft shadows. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: conference_room → `episodes/K0467/refs/locations/conference_room.png`

Flow name: `ref_location_conference_room`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. A glass-walled meeting room with a long table and whiteboard. Cool fluorescents, brighter; reflections in glass walls. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: server_room_window → `episodes/K0467/refs/locations/server_room_window.png`

Flow name: `ref_location_server_room_window`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. A window looking into the company's server room. Blue and amber equipment lights inside, dimmer corridor light outside. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: whiteboard → `episodes/K0467/refs/props/whiteboard.png`

Flow name: `ref_prop_whiteboard`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Glass whiteboard with architecture diagrams in colored markers. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: sticky_notes → `episodes/K0467/refs/props/sticky_notes.png`

Flow name: `ref_prop_sticky_notes`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Neon sticky notes on Priya's desk with different options. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: coffee_cup → `episodes/K0467/refs/props/coffee_cup.png`

Flow name: `ref_prop_coffee_cup`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Half-empty coffee cup with lipstick marks. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: closed_laptop → `episodes/K0467/refs/props/closed_laptop.png`

Flow name: `ref_prop_closed_laptop`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Closed laptop placed face-down (Ravi's determined gesture). Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Shot 1 image → `episodes/K0467/images/shot01.png`

Flow name: `K0467_shot01_image`
References, in this order: `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/office_cubicle.png`, `episodes/K0467/refs/props/sticky_notes.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Prop, sticky notes: Neon sticky notes on Priya's desk with different options.
Prop, coffee cup: Half-empty coffee cup with lipstick marks.
Shot: Close-up of Priya at her tech office desk, neon sticky notes spread across the desk surface with options written on them. Her expression is anxious, eyes focused on her monitor, one hand raised to her chin in a worried gesture. Cool fluorescent office lighting mixed with warm window light from the left. Camera: Medium close-up, slight push-in on Priya's face reflecting monitor light.
Reference images: image 1 is Priya; image 2 is the place (office_cubicle); image 3 is the sticky notes. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 2 image → `episodes/K0467/images/shot02.png`

Flow name: `K0467_shot02_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/conference_room.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A glass-walled meeting room with a long table and whiteboard. Light: Cool fluorescents, brighter; reflections in glass walls. Staging: Ravi stands by the whiteboard on the right, Priya sits at the table on the left.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Prop, whiteboard: Glass whiteboard with architecture diagrams in colored markers.
Shot: Conference room with glass walls. Ravi stands by a whiteboard with architecture diagrams in colored markers, pointing at one system with calm confidence. Priya sits at the table facing him, pen in hand, leaning forward with uncertain expression. Camera: Two-shot from slight angle, Ravi dominant on right.
Reference images: image 1 is Ravi; image 2 is Priya; image 3 is the place (conference_room). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 3 image → `episodes/K0467/images/shot03.png`

Flow name: `K0467_shot03_image`
References, in this order: `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/office_cubicle.png`, `episodes/K0467/refs/props/sticky_notes.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Prop, sticky notes: Neon sticky notes on Priya's desk with different options.
Shot: Priya at her desk typing rapidly, then turning in her chair toward Ravi's adjacent desk. Her hair is messed, one strand loose from her pin. Multiple documents and sticky notes scattered across her workspace. Camera: Side profile, Priya's stressed posture visible, swivel motion clear.
Reference images: image 1 is Priya; image 2 is the place (office_cubicle); image 3 is the sticky notes. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 4 image → `episodes/K0467/images/shot04.png`

Flow name: `K0467_shot04_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/office_cubicle.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Shot: Ravi at his desk looking at his monitor, Priya leaning over from her desk to talk to him. His expression patient but shoulders gradually tensing. Office background shows glass conference rooms out of focus. Camera: Over-the-shoulder from Ravi's perspective, Priya's face hopeful/anxious.
Reference images: image 1 is Ravi; image 2 is Priya; image 3 is the place (office_cubicle). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 5 image → `episodes/K0467/images/shot05.png`

Flow name: `K0467_shot05_image`
References, in this order: `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/office_cubicle.png`, `episodes/K0467/refs/props/coffee_cup.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Prop, coffee cup: Half-empty coffee cup with lipstick marks.
Prop, sticky notes: Neon sticky notes on Priya's desk with different options.
Shot: Priya at her desk covering her face with both hands in frustration. Her shoulders are tensed. Front-side angle view. Multiple sticky notes visible, empty coffee cup on desk corner. Camera: Close-up on Priya's face, eyes visible between fingers, then pulling hands away.
Reference images: image 1 is Priya; image 2 is the place (office_cubicle); image 3 is the coffee cup. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 6 image → `episodes/K0467/images/shot06.png`

Flow name: `K0467_shot06_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/locations/office_cubicle.png`, `episodes/K0467/refs/props/closed_laptop.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Prop, closed laptop: Closed laptop placed face-down (Ravi's determined gesture).
Shot: Ravi at his desk closing his laptop with a firm motion, then standing up. His expression shows calm, kind determination. He adjusts his polo shirt sleeves. Office behind him slightly blurred. Camera: Low angle, looking up at Ravi standing, determined and calm.
Reference images: image 1 is Ravi; image 2 is the place (office_cubicle); image 3 is the closed laptop. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 7 image → `episodes/K0467/images/shot07.png`

Flow name: `K0467_shot07_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/server_room_window.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A window looking into the company's server room. Light: Blue and amber equipment lights inside, dimmer corridor light outside. Staging: Both characters stand at the window looking in.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Shot: Ravi and Priya at a window looking into a server room. Inside, racks of servers glow with blue and amber lights. Ravi is pointing, talking calmly with kind expression. Priya's reflection shows her listening intently, anxious expression softening. Camera: Two-shot, reflections in glass window, blue and amber equipment lights inside.
Reference images: image 1 is Ravi; image 2 is Priya; image 3 is the place (server_room_window). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 8 image → `episodes/K0467/images/shot08.png`

Flow name: `K0467_shot08_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/locations/conference_room.png`, `episodes/K0467/refs/props/whiteboard.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A glass-walled meeting room with a long table and whiteboard. Light: Cool fluorescents, brighter; reflections in glass walls. Staging: Ravi stands by the whiteboard on the right, Priya sits at the table on the left.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Prop, whiteboard: Glass whiteboard with architecture diagrams in colored markers.
Shot: Ravi in conference room at the whiteboard, writing Tamil text with black marker. His posture is teaching-like, calm and instructive. Whiteboard shows kural in Tamil script as he writes. Camera: Medium shot, Ravi in profile, marker moving across whiteboard, contemplative.
Reference images: image 1 is Ravi; image 2 is the place (conference_room); image 3 is the whiteboard. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 9 image → `episodes/K0467/images/shot09.png`

Flow name: `K0467_shot09_image`
References, in this order: `episodes/K0467/refs/characters/ravi.png`, `episodes/K0467/refs/characters/priya.png`, `episodes/K0467/refs/locations/office_cubicle.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A tech company's open-plan office with modular desks. Light: Cool fluorescent overhead lights mixed with warm window light; soft shadows. Staging: Ravi's desk is on the right, Priya's is on the left; glass conference rooms are behind them.
Ravi: Medium height, athletic build, medium-brown skin, short curly black hair, clean-shaven, calm dark eyes. Wearing (same in every shot): Light grey polo shirt, dark jeans, simple black watch.
Priya: Medium height, slim, wheatish skin, long thick black hair in plait, silver hoop earrings, expressive face. Wearing (same in every shot): White shirt with loose black blazer, dark trousers, silver hoop earrings.
Prop, sticky notes: Neon sticky notes on Priya's desk with different options.
Shot: Wide shot of office cubicles showing Ravi and Priya at adjacent desks, both typing with focus and determination. Priya's posture is straight and confident. Sticky notes consolidated into one clear list. Warm window light mixes gently with cool fluorescent office lighting. Camera: Wide shot of both desks, side by side, each absorbed in work.
Reference images: image 1 is Ravi; image 2 is Priya; image 3 is the place (office_cubicle). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Day 1 · shot 1 clip (4 s, 7 credits) → `episodes/K0467/clips/shot01.mp4`

Flow name: `K0467_shot01_clip`
Start frame: `episodes/K0467/images/shot01.png`
Aspect 9:16 · Omni Flash 720p

```
Priya's eyes dart from sticky note to monitor; she picks up her coffee cup, realizes it's cold, sets it back; her jaw clenches. Camera: Medium close-up, slight push-in on Priya's face reflecting monitor light. About 4 seconds, one continuous shot, no cuts. From about 0.5 s, Priya says this line aloud in the natural voice of a 26-year-old Tamil backend developer, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "நாலணா மணிக்குள்ல backend system வேலை முடிய வேண்டும். ப்ரியாவுக்கு எந்த solution தேர்வு செய்য வேண்டுமோ அதுவே தெரியல." Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 2 clip (8 s, 12 credits) → `episodes/K0467/clips/shot02.mp4`

Flow name: `K0467_shot02_clip`
Start frame: `episodes/K0467/images/shot02.png`
Aspect 9:16 · Omni Flash 720p

```
Ravi's hand traces diagram lines smoothly; Priya nods but her fingers fidget with the pen. Camera: Two-shot from slight angle, Ravi dominant on right. About 8 seconds, one continuous shot, no cuts. From about 0.5 s, Ravi says this line aloud in the natural voice of a 32-year-old Tamil senior software developer, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "சீனியர் டெவலப்பர் ராவி வந்து சொல்றான்: ப்ரியா, இந்த architecture தான் சரி. நான் implementation முழுசுக் கவர் பண்ணுறேன்." Meanwhile Priya keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 3 clip (4 s, 7 credits) → `episodes/K0467/clips/shot03.mp4`

Flow name: `K0467_shot03_clip`
Start frame: `episodes/K0467/images/shot03.png`
Aspect 9:16 · Omni Flash 720p

```
Quick typing motions, then Priya stops, thinks, and swivels her chair smoothly. Camera: Side profile, Priya's stressed posture visible, swivel motion clear. About 4 seconds, one continuous shot, no cuts. From 0 s to 4 s Priya is talking: lips and jaw move clearly as if speaking, with small natural gestures. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 4 clip (8 s, 12 credits) → `episodes/K0467/clips/shot04.mp4`

Flow name: `K0467_shot04_clip`
Start frame: `episodes/K0467/images/shot04.png`
Aspect 9:16 · Omni Flash 720p

```
Priya leans toward Ravi; Ravi turns to face her, nodding slowly; his hands rest on desk, fingers tap once; he leans back. Camera: Over-the-shoulder from Ravi's perspective, Priya's face hopeful/anxious. About 8 seconds, one continuous shot, no cuts. From 0 s to 2 s Priya is talking: lips and jaw move clearly as if speaking, with small natural gestures. Ravi keeps their mouth closed and listens. From 2 s to 6 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Priya keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 5 clip (8 s, 12 credits) → `episodes/K0467/clips/shot05.mp4`

Flow name: `K0467_shot05_clip`
Start frame: `episodes/K0467/images/shot05.png`
Aspect 9:16 · Omni Flash 720p

```
Priya covers her face and takes a deep breath, hands slowly lowering; she leans back in chair with defeated expression. Camera: Close-up on Priya's face, eyes visible between fingers, then pulling hands away. About 8 seconds, one continuous shot, no cuts. From 0 s to 2 s nobody on screen talks: every mouth stays closed. From 2 s to 6 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 6 clip (8 s, 12 credits) → `episodes/K0467/clips/shot06.mp4`

Flow name: `K0467_shot06_clip`
Start frame: `episodes/K0467/images/shot06.png`
Aspect 9:16 · Omni Flash 720p

```
Ravi's hands close the laptop firmly; he stands slowly, pushing his chair back; he adjusts his sleeves and walks toward Priya. Camera: Low angle, looking up at Ravi standing, determined and calm. About 8 seconds, one continuous shot, no cuts. From 0 s to 1 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. From 1 s to 6 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 7 clip (8 s, 12 credits) → `episodes/K0467/clips/shot07.mp4`

Flow name: `K0467_shot07_clip`
Start frame: `episodes/K0467/images/shot07.png`
Aspect 9:16 · Omni Flash 720p

```
Ravi gestures at servers; Priya nods slowly; their reflections move in glass; server lights provide ambient motion. Camera: Two-shot, reflections in glass window, blue and amber equipment lights inside. About 8 seconds, one continuous shot, no cuts. From 0 s to 4 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Priya keeps their mouth closed and listens. From 4 s to 6 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Priya keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 8 clip (8 s, 12 credits) → `episodes/K0467/clips/shot08.mp4`

Flow name: `K0467_shot08_clip`
Start frame: `episodes/K0467/images/shot08.png`
Aspect 9:16 · Omni Flash 720p

```
Ravi's hand moves smoothly across whiteboard, writing each line of kural; camera pans slightly to follow the writing. Camera: Medium shot, Ravi in profile, marker moving across whiteboard, contemplative. About 8 seconds, one continuous shot, no cuts. From 0 s to 6 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 9 clip (4 s, 7 credits) → `episodes/K0467/clips/shot09.mp4`

Flow name: `K0467_shot09_clip`
Start frame: `episodes/K0467/images/shot09.png`
Aspect 9:16 · Omni Flash 720p

```
Priya types steadily with purpose; Ravi glances over with calm, satisfied smile, then focuses on work; both characters' shoulders relaxed now. Camera: Wide shot of both desks, side by side, each absorbed in work. About 4 seconds, one continuous shot, no cuts. From 0 s to 1 s Ravi is talking: lips and jaw move clearly as if speaking, with small natural gestures. Priya keeps their mouth closed and listens. From 1 s to 3 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```
