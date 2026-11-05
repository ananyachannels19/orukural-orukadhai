# Flow jobs for K1330

Make each item in Google Flow and save it to `save_as` (paths are relative to the repo). **No Flow project yet for K1330.** Before the first image, ask the user to create one in Flow named "K1330 – The coffee powder and the little sulk" and send its link, then record it with `python studio.py flow-project 1330 <link>`. Do not make anything until it is set.

**Never generate the same thing twice.** Every job has a `flow_name`. Before generating, search the Flow project for an asset with that name (or the same prompt); if it exists, download it to `save_as` instead. Name each new generation with its `flow_name`. If Flow or the tool reports an error or timeout, look in the project first: Flow often finishes jobs that were reported as failed. Only then retry.

**Never wait idle.** While a job runs, check the Flow page every 30-60 s. A failed tile, or no progress after 2 min (image) or 4 min (clip), counts as a failure: look for a finished result, then retry up to 2 times. Post a one-line note after each finished clip. If Flow shows "unusual activity", stop and tell the user; never try to get around it.

**Clip frames come from the project.** For a clip's start (and any end) frame, pick the existing image tile in the Flow project (search or scroll the picker by flow name). Upload or generate only if it is truly missing, and then only once. **Delete failed tiles** (failed generations with no usable result); never delete a successful image or clip without the user's say-so.

**Log every job for the live dashboard:** `python studio.py event 1330 <stage> <status> --shot N --attempt K --credits C --credits-left L --detail "..."`, with stage refs/images/image_check/clips/clip_check and status start/done/fail/retry/blocked. Log credits_left from Flow after every clip.

Work in this order:

1. **References** (characters, places, props). The episode's own cast and places are made for this episode (`refs/`); series ones are made once and reused.
2. **Shot images**, attaching every listed reference image in the listed order.
3. **Image review.** Run `python studio.py continuity-sheet 1330` and follow the continuity-review skill (`.claude/skills/continuity-review/SKILL.md`): compare every image with the references, redo any that drift (images are free), and mark each one `pass` in `episodes/K1330/continuity_review.json`. Do not start clips until every image passes; clips cost credits.
4. **Clips**, from the reviewed images. They need 64 credits over 1 day(s): 1050 daily credits a day. Spend daily credits before monthly ones. Make only today's day number; if credits run out, stop and continue after the reset. Never buy credits.
5. **Clip review.** Run `continuity-sheet 1330` again, check the first, middle and last frames of each clip, and mark clips `pass`. Redo a drifting clip only if credits allow; otherwise note it and tell the user.
6. Run `python studio.py visuals 1330`, then `render 1330`.

## Character reference: kathir → `episodes/K1330/refs/characters/kathir.png`

Flow name: `ref_character_kathir`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Kathir, a 30-year-old Tamil pharmacist at a neighbourhood medical shop. Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Character reference: mithra → `episodes/K1330/refs/characters/mithra.png`

Flow name: `ref_character_mithra`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Mithra, a 27-year-old Tamil runs a blouse-stitching tailoring business from home. Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: flat_hall → `episodes/K1330/refs/locations/flat_hall.png`

Flow name: `ref_location_flat_hall`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. A small rented first-floor flat in a Tamil Nadu town: a hall with a small wooden dining table and two chairs, a sewing machine with folded blouse pieces on a side table, the open kitchen counter behind with a steel coffee filter and a gas stove, the front door on the right with a shoe rack, rain streaking the window. 9:40 pm, warm white tube light inside; dark rainy night outside the window. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: street_shop → `episodes/K1330/refs/locations/street_shop.png`

Flow name: `ref_location_street_shop`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. The wet street below the flat: a small provision shop with its shutter half down, sacks and glass jars inside, a single yellow streetlight, puddles reflecting the light, signs with no readable words. Night, heavy rain, yellow streetlight and the shop's single bulb. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: balcony → `episodes/K1330/refs/locations/balcony.png`

Flow name: `ref_location_balcony`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. The flat's narrow balcony: a low parapet wall with a few potted tulsi and jasmine plants, a plastic chair, a clothesline, rain falling beyond the parapet onto the street below. Night, rain, warm light spilling out from the hall door behind them. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: tumbler → `episodes/K1330/refs/props/tumbler.png`

Flow name: `ref_prop_tumbler`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: One stainless-steel tumbler and davara (filter-coffee cup and saucer), plain and shiny. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: coffee_packet → `episodes/K1330/refs/props/coffee_packet.png`

Flow name: `ref_prop_coffee_packet`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: A small brown paper packet of coffee powder folded at the top, no writing, wet with rain. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: scooter → `episodes/K1330/refs/props/scooter.png`

Flow name: `ref_prop_scooter`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Kathir's plain teal scooter with a black seat, no logos or writing. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: towel → `episodes/K1330/refs/props/towel.png`

Flow name: `ref_prop_towel`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: A thin white cotton towel with a red border. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Shot 1 image → `episodes/K1330/images/shot01.png`

Flow name: `K1330_shot01_image`
References, in this order: `episodes/K1330/refs/characters/mithra.png`, `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/locations/flat_hall.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A small rented first-floor flat in a Tamil Nadu town: a hall with a small wooden dining table and two chairs, a sewing machine with folded blouse pieces on a side table, the open kitchen counter behind with a steel coffee filter and a gas stove, the front door on the right with a shoe rack, rain streaking the window. Light: 9:40 pm, warm white tube light inside; dark rainy night outside the window. Staging: Mithra at the dining table on the left, facing right; Kathir at the front door on the right, facing her; in the kitchen Kathir stands at the counter on the right, Mithra on the left.
Mithra: Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. Wearing (same in every shot): A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Prop, tumbler: One stainless-steel tumbler and davara (filter-coffee cup and saucer), plain and shiny.
Shot: Mithra at the dining table on the left, mid-motion setting the steel tumbler down hard, frowning at Kathir; Kathir in the open front doorway on the right, office bag on his shoulder, frozen with a guilty half-smile. Camera: Static medium shot from the kitchen side, eye level, Mithra in front, Kathir in the doorway behind.
Reference images: image 1 is Mithra; image 2 is Kathir; image 3 is the place (flat_hall). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 3 image → `episodes/K1330/images/shot03.png`

Flow name: `K1330_shot03_image`
References, in this order: `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/locations/flat_hall.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A small rented first-floor flat in a Tamil Nadu town: a hall with a small wooden dining table and two chairs, a sewing machine with folded blouse pieces on a side table, the open kitchen counter behind with a steel coffee filter and a gas stove, the front door on the right with a shoe rack, rain streaking the window. Light: 9:40 pm, warm white tube light inside; dark rainy night outside the window. Staging: Mithra at the dining table on the left, facing right; Kathir at the front door on the right, facing her; in the kitchen Kathir stands at the counter on the right, Mithra on the left.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Shot: Kathir at the open front door, his office bag just set down on the shoe rack, picking a key off a wall hook, rain visible on the stairs outside. Camera: Medium shot from inside the hall towards the front door.
Reference images: image 1 is Kathir; image 2 is the place (flat_hall). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 4 image → `episodes/K1330/images/shot04.png`

Flow name: `K1330_shot04_image`
References, in this order: `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/locations/street_shop.png`, `episodes/K1330/refs/props/scooter.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The wet street below the flat: a small provision shop with its shutter half down, sacks and glass jars inside, a single yellow streetlight, puddles reflecting the light, signs with no readable words. Light: Night, heavy rain, yellow streetlight and the shop's single bulb. Staging: Kathir parks his scooter on the left and stands at the shop counter on the right; the shopkeeper is only a hand passing the packet.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Prop, scooter: Kathir's plain teal scooter with a black seat, no logos or writing.
Prop, coffee packet: A small brown paper packet of coffee powder folded at the top, no writing, wet with rain.
Shot: Kathir, hair and shirt soaked, stands at the half-shuttered provision shop under its single bulb, his teal scooter parked on the left in a puddle, holding out his hand towards the counter. Camera: Medium shot from the street, eye level, rain falling between camera and Kathir.
Reference images: image 1 is Kathir; image 2 is the place (street_shop); image 3 is the scooter. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 5 image → `episodes/K1330/images/shot05.png`

Flow name: `K1330_shot05_image`
References, in this order: `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/characters/mithra.png`, `episodes/K1330/refs/locations/flat_hall.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A small rented first-floor flat in a Tamil Nadu town: a hall with a small wooden dining table and two chairs, a sewing machine with folded blouse pieces on a side table, the open kitchen counter behind with a steel coffee filter and a gas stove, the front door on the right with a shoe rack, rain streaking the window. Light: 9:40 pm, warm white tube light inside; dark rainy night outside the window. Staging: Mithra at the dining table on the left, facing right; Kathir at the front door on the right, facing her; in the kitchen Kathir stands at the counter on the right, Mithra on the left.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Mithra: Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. Wearing (same in every shot): A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists.
Prop, coffee packet: A small brown paper packet of coffee powder folded at the top, no writing, wet with rain.
Shot: Kathir in the front doorway, completely drenched, water dripping from his hair and shirt, holding up the small brown paper packet with a proud grin; Mithra in the foreground on the left, back half-turned, glancing at him from the corner of her eye. Camera: Medium shot from beside the dining table, Mithra's shoulder in the foreground, Kathir at the door.
Reference images: image 1 is Kathir; image 2 is Mithra; image 3 is the place (flat_hall). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 6 image → `episodes/K1330/images/shot06.png`

Flow name: `K1330_shot06_image`
References, in this order: `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/characters/mithra.png`, `episodes/K1330/refs/locations/flat_hall.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: A small rented first-floor flat in a Tamil Nadu town: a hall with a small wooden dining table and two chairs, a sewing machine with folded blouse pieces on a side table, the open kitchen counter behind with a steel coffee filter and a gas stove, the front door on the right with a shoe rack, rain streaking the window. Light: 9:40 pm, warm white tube light inside; dark rainy night outside the window. Staging: Mithra at the dining table on the left, facing right; Kathir at the front door on the right, facing her; in the kitchen Kathir stands at the counter on the right, Mithra on the left.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Mithra: Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. Wearing (same in every shot): A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists.
Prop, tumbler: One stainless-steel tumbler and davara (filter-coffee cup and saucer), plain and shiny.
Prop, towel: A thin white cotton towel with a red border.
Shot: In the kitchen, Kathir on the right with the white towel over his wet head, holding out the steel tumbler and davara with both hands to Mithra on the left, who stands with arms still folded, eyebrows raised. Camera: Static medium two-shot at the kitchen counter, eye level, both faces in view.
Reference images: image 1 is Kathir; image 2 is Mithra; image 3 is the place (flat_hall). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 7 image → `episodes/K1330/images/shot07.png`

Flow name: `K1330_shot07_image`
References, in this order: `episodes/K1330/refs/characters/mithra.png`, `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/locations/balcony.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The flat's narrow balcony: a low parapet wall with a few potted tulsi and jasmine plants, a plastic chair, a clothesline, rain falling beyond the parapet onto the street below. Light: Night, rain, warm light spilling out from the hall door behind them. Staging: Mithra on the left, Kathir on the right, both sitting on the parapet's low ledge facing the rain, shoulder to shoulder.
Mithra: Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. Wearing (same in every shot): A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Prop, tumbler: One stainless-steel tumbler and davara (filter-coffee cup and saucer), plain and shiny.
Prop, towel: A thin white cotton towel with a red border.
Shot: Mithra and Kathir sitting close on the balcony ledge facing the rain, Mithra on the left holding the steel tumbler in both hands, her head resting on Kathir's shoulder; Kathir on the right, the white towel around his shoulders. Camera: Medium wide shot from behind and slightly to the side, the rain and the street lights beyond them.
Reference images: image 1 is Mithra; image 2 is Kathir; image 3 is the place (balcony). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 8 image → `episodes/K1330/images/shot08.png`

Flow name: `K1330_shot08_image`
References, in this order: `episodes/K1330/refs/characters/mithra.png`, `episodes/K1330/refs/characters/kathir.png`, `episodes/K1330/refs/locations/balcony.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The flat's narrow balcony: a low parapet wall with a few potted tulsi and jasmine plants, a plastic chair, a clothesline, rain falling beyond the parapet onto the street below. Light: Night, rain, warm light spilling out from the hall door behind them. Staging: Mithra on the left, Kathir on the right, both sitting on the parapet's low ledge facing the rain, shoulder to shoulder.
Mithra: Medium height, round face, dusky skin, long thick black hair in a loose single plait, a small gold nose stud, a small black bindi, expressive eyebrows. Wearing (same in every shot): A peach cotton salwar kameez with a plain white dupatta over one shoulder, a measuring tape around her neck, glass bangles on both wrists.
Kathir: Tall and slim, square jaw, light-brown skin, very short crew-cut black hair, a thick black moustache, no beard, no glasses, a dimple when he smiles. Wearing (same in every shot): A light-yellow formal half-sleeve shirt, dark-grey trousers, black sandals.
Prop, tumbler: One stainless-steel tumbler and davara (filter-coffee cup and saucer), plain and shiny.
Shot: Close-up of Mithra's hand with glass bangles and Kathir's hand together around the one steel tumbler, rain drops blurred behind them. Camera: Close-up on hands and tumbler, shallow depth of field.
Reference images: image 1 is Mithra; image 2 is Kathir; image 3 is the place (balcony). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Day 1 · shot 1 clip (8 s, 12 credits) → `episodes/K1330/clips/shot01.mp4`

Flow name: `K1330_shot01_clip`
Start frame: `episodes/K1330/images/shot01.png`
Aspect 9:16 · Omni Flash 720p

```
Mithra sets the tumbler down with a firm tap and speaks sharply to Kathir; then she turns her chair away from him and folds her arms, chin up. Kathir rubs the back of his neck, looks at the window where rain is falling, and nods to himself. Exactly one tumbler in the shot; nothing else changes hands. Camera: Static medium shot from the kitchen side, eye level, Mithra in front, Kathir in the doorway behind. About 8 seconds, one continuous shot, no cuts. From about 0.5 s, Mithra says this line aloud in a firm, clear 27-year-old Tamil woman's voice that softens into laughter, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "மூணாவது தடவை மறந்துட்டீங்க!" Meanwhile Kathir keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Shot 2 (3–7 s): no new generation

Uses seconds 3–7 of shot 1's clip. On screen: Mithra sits with her back to Kathir, arms folded, refusing to talk.
Over it: narrator: மித்ரா அதுக்கு மேல ஒரு வார்த்தை பேசல. திரும்பி உக்காந்துட்டா.

## Shot 9 (37–41 s): no new generation

Uses seconds 0–4 of shot 1's clip. On screen: Back to the start: Mithra setting the tumbler down hard, so the replay flows into her opening line.
Over it: narrator: சண்டை சின்னதா இருக்கட்டும். சமாதானம் சூடா இருக்கட்டும். / narrator: சண்டைக்கு அப்புறம் காபி போடுற உங்க ஆள டேக் பண்ணுங்க!

## Day 1 · shot 3 clip (4 s, 7 credits) → `episodes/K1330/clips/shot03.mp4`

Flow name: `K1330_shot03_clip`
Start frame: `episodes/K1330/images/shot03.png`
Aspect 9:16 · Omni Flash 720p

```
Kathir takes the key, glances back once at the hall, and steps out of the door into the rainy stairway, leaving the umbrella on the rack. Nobody speaks. Camera: Medium shot from inside the hall towards the front door. About 4 seconds, one continuous shot, no cuts. From 0 s to 3 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 4 clip (4 s, 7 credits) → `episodes/K1330/clips/shot04.mp4`

Flow name: `K1330_shot04_clip`
Start frame: `episodes/K1330/images/shot04.png`
Aspect 9:16 · Omni Flash 720p

```
A hand from inside the shop passes him a small brown paper packet; Kathir tucks it inside his shirt to keep it dry, grins, and turns back to the scooter. Rain pours steadily. Camera: Medium shot from the street, eye level, rain falling between camera and Kathir. About 4 seconds, one continuous shot, no cuts. From 0 s to 4 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 5 clip (4 s, 7 credits) → `episodes/K1330/clips/shot05.mp4`

Flow name: `K1330_shot05_clip`
Start frame: `episodes/K1330/images/shot05.png`
Aspect 9:16 · Omni Flash 720p

```
Kathir lifts the packet a little higher and raises his eyebrows; water drips onto the floor. Mithra quickly looks away again, pressing her lips together to hide a smile. Nobody speaks. Camera: Medium shot from beside the dining table, Mithra's shoulder in the foreground, Kathir at the door. About 4 seconds, one continuous shot, no cuts. From 0 s to 4 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 6 clip (8 s, 12 credits) → `episodes/K1330/clips/shot06.mp4`

Flow name: `K1330_shot06_clip`
Start frame: `episodes/K1330/images/shot06.png`
Aspect 9:16 · Omni Flash 720p

```
Kathir speaks first with a hopeful smile and offers the tumbler; Mithra takes it, sips, scrunches up her face and speaks, then cannot hold it in and laughs, covering her mouth; Kathir laughs with her. Exactly one tumbler, passed once from Kathir to Mithra. Camera: Static medium two-shot at the kitchen counter, eye level, both faces in view. About 8 seconds, one continuous shot, no cuts. From about 0.5 s, Kathir says this line aloud in a clear, light, playful 30-year-old Tamil man's voice, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "மேடம், காபி ரெடி. கோபம் இன்னும் எவ்வளவு நேரம்?" Meanwhile Mithra keeps their mouth closed and listens. From about 4.0 s, Mithra says this line aloud in a firm, clear 27-year-old Tamil woman's voice that softens into laughter, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "ஐயோ... இது காபியா, கஷாயமா?" Meanwhile Kathir keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 7 clip (8 s, 12 credits) → `episodes/K1330/clips/shot07.mp4`

Flow name: `K1330_shot07_clip`
Start frame: `episodes/K1330/images/shot07.png`
Aspect 9:16 · Omni Flash 720p

```
Kathir lifts one side of the towel and wraps it around Mithra's shoulders too; she smiles and passes him the tumbler; he sips and passes it back. Rain falls steadily. Nobody speaks. Camera: Medium wide shot from behind and slightly to the side, the rain and the street lights beyond them. About 8 seconds, one continuous shot, no cuts. From 0 s to 7 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 8 clip (4 s, 7 credits) → `episodes/K1330/clips/shot08.mp4`

Flow name: `K1330_shot08_clip`
Start frame: `episodes/K1330/images/shot08.png`
Aspect 9:16 · Omni Flash 720p

```
Kathir's thumb gently taps Mithra's fingers; her bangles clink softly; a little steam rises from the tumbler. Camera: Close-up on hands and tumbler, shallow depth of field. About 4 seconds, one continuous shot, no cuts. From 0 s to 2 s nobody on screen talks: every mouth stays closed. From 2 s to 4 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```
