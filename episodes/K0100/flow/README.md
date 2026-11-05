# Flow jobs for K0100

Make each item in Google Flow and save it to `save_as` (paths are relative to the repo). Use this episode's own Flow project, "K0100 – The Deepavali kolam and a brother's words": https://flow.google.com/u/1/project/79afd990-d322-4100-871c-d97938a32a86

**Never generate the same thing twice.** Every job has a `flow_name`. Before generating, search the Flow project for an asset with that name (or the same prompt); if it exists, download it to `save_as` instead. Name each new generation with its `flow_name`. If Flow or the tool reports an error or timeout, look in the project first: Flow often finishes jobs that were reported as failed. Only then retry.

**Never wait idle.** While a job runs, check the Flow page every 30-60 s. A failed tile, or no progress after 2 min (image) or 4 min (clip), counts as a failure: look for a finished result, then retry up to 2 times. Post a one-line note after each finished clip. If Flow shows "unusual activity", stop and tell the user; never try to get around it.

**Clip frames come from the project.** For a clip's start (and any end) frame, pick the existing image tile in the Flow project (search or scroll the picker by flow name). Upload or generate only if it is truly missing, and then only once. **Delete failed tiles** (failed generations with no usable result); never delete a successful image or clip without the user's say-so.

**Log every job for the live dashboard:** `python studio.py event 100 <stage> <status> --shot N --attempt K --credits C --credits-left L --detail "..."`, with stage refs/images/image_check/clips/clip_check and status start/done/fail/retry/blocked. Log credits_left from Flow after every clip.

Work in this order:

1. **References** (characters, places, props). The episode's own cast and places are made for this episode (`refs/`); series ones are made once and reused.
2. **Shot images**, attaching every listed reference image in the listed order.
3. **Image review.** Run `python studio.py continuity-sheet 100` and follow the continuity-review skill (`.claude/skills/continuity-review/SKILL.md`): compare every image with the references, redo any that drift (images are free), and mark each one `pass` in `episodes/K0100/continuity_review.json`. Do not start clips until every image passes; clips cost credits.
4. **Clips**, from the reviewed images. They need 71 credits over 1 day(s): 1050 daily credits a day. Spend daily credits before monthly ones. Make only today's day number; if credits run out, stop and continue after the reset. Never buy credits.
5. **Clip review.** Run `continuity-sheet 100` again, check the first, middle and last frames of each clip, and mark clips `pass`. Redo a drifting clip only if credits allow; otherwise note it and tell the user.
6. Run `python studio.py visuals 100`, then `render 100`.

## Character reference: kayal → `episodes/K0100/refs/characters/kayal.png`

Flow name: `ref_character_kayal`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Kayal, a 22-year-old Tamil final-year B.Com student. Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Character reference: muthu → `episodes/K0100/refs/characters/muthu.png`

Flow name: `ref_character_muthu`
Aspect 1:1 · Nano Banana 2 Lite

```
Character reference sheet for an animated series. Muthu, a 28-year-old Tamil government town-bus conductor. Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals. Show the same character twice side by side: full body standing front view, and a head-and-shoulders close-up. Neutral expression. Plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Place reference: house_front → `episodes/K0100/refs/locations/house_front.png`

Flow name: `ref_location_house_front`
Aspect 9:16 · Nano Banana 2 Lite

```
Location reference plate for an animated series, vertical 9:16, wide establishing view, no people. The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: kolam → `episodes/K0100/refs/props/kolam.png`

Flow name: `ref_prop_kolam`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: powder_bowl → `episodes/K0100/refs/props/powder_bowl.png`

Flow name: `ref_prop_powder_bowl`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: A small round brass bowl full of white kolam powder. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: diyas → `episodes/K0100/refs/props/diyas.png`

Flow name: `ref_prop_diyas`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Small terracotta clay diyas with cotton wicks, each with a small steady flame once lit. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Prop reference: bag → `episodes/K0100/refs/props/bag.png`

Flow name: `ref_prop_bag`
Aspect 1:1 · Nano Banana 2 Lite

```
Prop reference for an animated series: Muthu's worn brown leather conductor's bag on a strap across his chest, no writing. Shown alone, whole, centred, three-quarter view on a plain light warm-grey background. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
```

## Shot 1 image → `episodes/K0100/images/shot01.png`

Flow name: `K0100_shot01_image`
References, in this order: `episodes/K0100/refs/characters/muthu.png`, `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Muthu: Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. Wearing (same in every shot): A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Prop, powder bowl: A small round brass bowl full of white kolam powder.
Prop, bag: Muthu's worn brown leather conductor's bag on a strap across his chest, no writing.
Shot: Muthu standing at the gate side of the yard in his khaki uniform with the bag across his chest, frowning down at the kolam towards the camera, face clearly visible; Kayal kneeling at the right edge of frame beside the kolam holding the brass bowl, looking up at him. Camera: Low static medium shot from the kolam's edge, looking up at Muthu, Kayal kneeling at the right edge of frame.
Reference images: image 1 is Muthu; image 2 is Kayal; image 3 is the place (house_front). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 2 image → `episodes/K0100/images/shot02.png`

Flow name: `K0100_shot02_image`
References, in this order: `episodes/K0100/refs/characters/muthu.png`, `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Muthu: Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. Wearing (same in every shot): A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Prop, powder bowl: A small round brass bowl full of white kolam powder.
Prop, bag: Muthu's worn brown leather conductor's bag on a strap across his chest, no writing.
Shot: Muthu standing on the left, frowning, pointing down at the uneven outer lines of the kolam; Kayal kneeling on the right with the brass bowl in her hands, her proud expression starting to fade, both faces in view. Camera: Static medium two-shot from the steps side, both faces in view.
Reference images: image 1 is Muthu; image 2 is Kayal; image 3 is the place (house_front). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 3 image → `episodes/K0100/images/shot03.png`

Flow name: `K0100_shot03_image`
References, in this order: `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`, `episodes/K0100/refs/props/powder_bowl.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, powder bowl: A small round brass bowl full of white kolam powder.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Shot: Close-up of Kayal's hand with glass bangles, a pinch of white kolam powder between her fingers above an unfinished line, the brass bowl in her other hand. Camera: Close-up on her hands and the kolam line, shallow depth of field.
Reference images: image 1 is Kayal; image 2 is the place (house_front); image 3 is the powder bowl. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 4 image → `episodes/K0100/images/shot04.png`

Flow name: `K0100_shot04_image`
References, in this order: `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`, `episodes/K0100/refs/props/kolam.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Shot: Kayal kneeling beside the kolam, looking up towards the camera, hurt but steady, her face fully in view, hands resting on her knees, nothing in her hands. Camera: Static medium close-up on Kayal from Muthu's side, her face fully to camera.
Reference images: image 1 is Kayal; image 2 is the place (house_front); image 3 is the kolam. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 5 image → `episodes/K0100/images/shot05.png`

Flow name: `K0100_shot05_image`
References, in this order: `episodes/K0100/refs/locations/house_front.png`, `episodes/K0100/refs/props/kolam.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Shot: Top-down view of the whole round kolam on the grey cement in morning light, the blue-and-green peacock at its exact centre, the tips of Muthu's sandals at the bottom edge of frame. Camera: Top-down view of the whole kolam, then a slow push-in towards the peacock at its centre.
Reference images: image 1 is the place (house_front); image 2 is the kolam. Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 6 image → `episodes/K0100/images/shot06.png`

Flow name: `K0100_shot06_image`
References, in this order: `episodes/K0100/refs/characters/muthu.png`, `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Muthu: Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. Wearing (same in every shot): A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Prop, bag: Muthu's worn brown leather conductor's bag on a strap across his chest, no writing.
Shot: Muthu crouching on the left beside the kolam, his bag pushed to his back, looking at the peacock and then at Kayal, his face softening; Kayal kneeling on the right, looking at him. Camera: Static medium two-shot at kolam level, both faces in view.
Reference images: image 1 is Muthu; image 2 is Kayal; image 3 is the place (house_front). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 7 image → `episodes/K0100/images/shot07.png`

Flow name: `K0100_shot07_image`
References, in this order: `episodes/K0100/refs/characters/muthu.png`, `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/locations/house_front.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Muthu: Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. Wearing (same in every shot): A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Prop, diyas: Small terracotta clay diyas with cotton wicks, each with a small steady flame once lit.
Shot: Muthu and Kayal kneeling side by side at the edge of the kolam in the golden morning light, Muthu sprinkling orange rangoli powder into a petal, Kayal guiding his hand, the row of lit clay diyas on the step in the foreground. Camera: Wide static shot from the steps, the sunrise behind the gate.
Reference images: image 1 is Muthu; image 2 is Kayal; image 3 is the place (house_front). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Shot 8 image → `episodes/K0100/images/shot08.png`

Flow name: `K0100_shot08_image`
References, in this order: `episodes/K0100/refs/characters/kayal.png`, `episodes/K0100/refs/characters/muthu.png`, `episodes/K0100/refs/locations/house_front.png`
Aspect 9:16 · Nano Banana 2 Lite

```
Vertical 9:16 frame. Style: Warm, painterly 3D animation look, soft golden-hour light, gentle film grain, expressive faces, shallow depth of field. Consistent across all episodes. No text inside generated images (we add Tamil text ourselves).
Place: The front of a small one-storey house in a Tamil Nadu town on Deepavali morning: a swept, dry, smooth grey cement front yard, two red-oxide steps up to a teak front door with a mango-leaf thoranam strung across the top, a low compound wall painted pale blue with a blue wooden gate on the left, a tulsi pot on a small stand by the steps, a row of small clay diyas along the edge of the top step. Light: Just after sunrise, soft golden sunlight from the left, long gentle shadows, a clear pale-blue sky; the diyas are lit from shot 7 on. Staging: The kolam lies in the middle of the yard; Kayal kneels on its right edge facing left; Muthu stands at the gate side on the left facing right, looking down at it.
Kayal: Slim, oval face, wheatish skin, shoulder-length wavy black hair in a half ponytail, a small red bindi, small silver jhumka earrings, no nose stud, large expressive eyes. Wearing (same in every shot): A mustard-yellow cotton churidar with a maroon dupatta tied around her waist, glass bangles in green and gold on both wrists, barefoot.
Muthu: Medium height, sturdy build, round face, medium-brown skin, short wavy black hair, clean-shaven, a small mole on his left cheek, tired eyes, no glasses. Wearing (same in every shot): A khaki conductor's half-sleeve shirt and khaki trousers, a brown leather conductor's bag on a strap across his chest, black sandals.
Prop, kolam: A large round Deepavali kolam about 1.5 m across drawn on the cement in white rice-flour lines with loops and dots, coloured with rangoli powder in magenta, orange and yellow, and in its exact centre a peacock in blue and green with a fanned tail; a few lines on its outer edge are slightly uneven.
Prop, diyas: Small terracotta clay diyas with cotton wicks, each with a small steady flame once lit.
Shot: Close shot of the finished blue-and-green peacock in the kolam, Kayal's hand with green and gold bangles placing a lit clay diya beside it, Muthu's hand above it with a pinch of yellow powder. Camera: Close shot on the peacock at kolam level, shallow depth of field.
Reference images: image 1 is Kayal; image 2 is Muthu; image 3 is the place (house_front). Match faces, hair, glasses, body, clothes, the place and every prop exactly as in them; do not copy their layout or background.
No text, letters, logos or subtitles anywhere in the image.
```

## Day 1 · shot 1 clip (4 s, 7 credits) → `episodes/K0100/clips/shot01.mp4`

Flow name: `K0100_shot01_clip`
Start frame: `episodes/K0100/images/shot01.png`
Aspect 9:16 · Omni Flash 720p

```
Muthu frowns and says his line sharply, facing the camera, irritated and tired, with no smile at any moment; Kayal holds still, mouth closed, looking up at him. Nothing else moves. Camera: Low static medium shot from the kolam's edge, looking up at Muthu, Kayal kneeling at the right edge of frame. About 4 seconds, one continuous shot, no cuts. From about 0.5 s, Muthu says this line aloud in a firm, tired 28-year-old Tamil man's voice, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "இதுக்கு பேரு கோலமா?" Meanwhile Kayal keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 2 clip (8 s, 12 credits) → `episodes/K0100/clips/shot02.mp4`

Flow name: `K0100_shot02_clip`
Start frame: `episodes/K0100/images/shot02.png`
Aspect 9:16 · Omni Flash 720p

```
For the first few seconds nobody speaks: Muthu looks over the kolam, frowning. Then Muthu says his line flatly, frowning, pointing at the edge; no smile at any moment. Kayal's face slowly falls; her mouth stays closed. The brass bowl stays in her two hands the whole time. Camera: Static medium two-shot from the steps side, both faces in view. About 8 seconds, one continuous shot, no cuts. From 0 s to 4 s nobody on screen talks: every mouth stays closed. From about 4.0 s, Muthu says this line aloud in a firm, tired 28-year-old Tamil man's voice, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "எல்லாம் கோணல் மாணலா இருக்கு." Meanwhile Kayal keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 3 clip (4 s, 7 credits) → `episodes/K0100/clips/shot03.mp4`

Flow name: `K0100_shot03_clip`
Start frame: `episodes/K0100/images/shot03.png`
Aspect 9:16 · Omni Flash 720p

```
Her fingers stop; a little powder falls; she slowly lowers the bowl onto the cement beside the kolam. Nobody speaks. Camera: Close-up on her hands and the kolam line, shallow depth of field. About 4 seconds, one continuous shot, no cuts. From 0 s to 4 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 4 clip (4 s, 7 credits) → `episodes/K0100/clips/shot04.mp4`

Flow name: `K0100_shot04_clip`
Start frame: `episodes/K0100/images/shot04.png`
Aspect 9:16 · Omni Flash 720p

```
Kayal says her line quietly, looking up into the camera, hurt but steady, no smile and no tears; her hands stay on her knees, nothing near her mouth. Camera: Static medium close-up on Kayal from Muthu's side, her face fully to camera. About 4 seconds, one continuous shot, no cuts. From about 0.5 s, Kayal says this line aloud in a bright, soft 21-year-old Tamil woman's voice, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "அண்ணா... இதுல ஒண்ணு கூடவா நல்லா இல்ல?" Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 5 clip (4 s, 7 credits) → `episodes/K0100/clips/shot05.mp4`

Flow name: `K0100_shot05_clip`
Start frame: `episodes/K0100/images/shot05.png`
Aspect 9:16 · Omni Flash 720p

```
Slow push-in from the whole kolam to the peacock at its centre; morning light; nothing else moves. Camera: Top-down view of the whole kolam, then a slow push-in towards the peacock at its centre. About 4 seconds, one continuous shot, no cuts. From 0 s to 4 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 6 clip (4 s, 7 credits) → `episodes/K0100/clips/shot06.mp4`

Flow name: `K0100_shot06_clip`
Start frame: `episodes/K0100/images/shot06.png`
Aspect 9:16 · Omni Flash 720p

```
Muthu says his line softly to Kayal, facing her and the camera, with a small apologetic smile; Kayal's face slowly lifts into a smile while her mouth stays closed. Nobody holds anything. Camera: Static medium two-shot at kolam level, both faces in view. About 4 seconds, one continuous shot, no cuts. From about 0.5 s, Muthu says this line aloud in a firm, tired 28-year-old Tamil man's voice, pronouncing every word exactly in clear standard Tamil, lips and jaw matching every word, the body acting it out, face in view while speaking: "மயில்... ரொம்ப அழகா இருக்கு, கயல்." Meanwhile Kayal keeps their mouth closed and listens. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the spoken line(s) above and the natural sounds of the scene; no music, no other voices.
```

## Day 1 · shot 7 clip (8 s, 12 credits) → `episodes/K0100/clips/shot07.mp4`

Flow name: `K0100_shot07_clip`
Start frame: `episodes/K0100/images/shot07.png`
Aspect 9:16 · Omni Flash 720p

```
They colour one petal together, Kayal smiling and pointing, Muthu nodding; the diya flames flicker gently. Nobody speaks; mouths closed. Camera: Wide static shot from the steps, the sunrise behind the gate. About 8 seconds, one continuous shot, no cuts. From 0 s to 7 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```

## Day 1 · shot 8 clip (8 s, 12 credits) → `episodes/K0100/clips/shot08.mp4`

Flow name: `K0100_shot08_clip`
Start frame: `episodes/K0100/images/shot08.png`
Aspect 9:16 · Omni Flash 720p

```
Kayal sets the diya down; Muthu drops a last dot of yellow powder on the peacock's crest; the flame flickers. Slow push-in. Camera: Close shot on the peacock at kolam level, shallow depth of field. About 8 seconds, one continuous shot, no cuts. From 0 s to 2 s nobody on screen talks: every mouth stays closed. From 2 s to 6 s nobody on screen talks: every mouth stays closed. From 6 s to 8 s nobody on screen talks: every mouth stays closed. Keep every character's face, hair, clothes and size, the place, the light and every object exactly as in the start frame; nothing appears, disappears or changes colour. No on-screen text. Sound: only the natural sounds of the scene (footsteps, engines, traffic, room tone, wind); no music, and no voice or speech is heard.
```
