---
name: continuity-review
description: Check an Orukural Orukadhai episode's Flow images and clips for character, place, prop and lighting continuity before clips are made and before rendering. Use after making shot images or clips in Flow, or when `studio.py assemble` says the continuity review has not passed.
---

# Continuity review

Every shot in an episode must look like the same world: the same faces, clothes, place, props and light, unless the story shows a change. Images are free in Flow, clips cost credits, so review images **before** making any clip.

## Steps

1. Run `python studio.py continuity-sheet <kural>`. It writes, under `episodes/<id>/flow/review/`:
   - `references.jpg`: every character, place and prop reference used in the episode
   - `images.jpg`: all shot images in order, labelled with place, characters and props
   - `clip_frames.jpg`: first, middle and last frame of every clip made so far
   It also creates `episodes/<id>/continuity_review.json` if missing.
2. Read `episodes/<id>/script.md` (the **Continuity** section is the bible: places, light, blocking, props, outfits) and look at the three sheets. Open single images in `episodes/<id>/images/` when you need detail.
3. Check each shot against the bible and the references:
   - **Characters**: same face, age, hair (Kavin's cowlick, Thatha's silver hair and beard), Thatha's round steel glasses and sandal-paste line, body size relative to each other.
   - **Outfits**: exactly the episode's outfit in every shot; nothing added or missing (shawl, backpack, shoes) unless the script changes it on screen.
   - **Place**: the landmarks of the place reference (pillars, neem tree, gate, lamp niche, colours) are there and in the same arrangement.
   - **Props**: same colour, size and markings in every shot (e.g. the puppy's floppy left ear and red string collar); an object that the story has put down stays down.
   - **Blocking and screen direction**: people are where `blocking_en` puts them and face the same way across cuts.
   - **Light**: matches the scene's `light_en`, and time only moves forward.
   - **No text**: no letters, signs or logos in the frame.
   - **Clips** (from `clip_frames.jpg`): the last frame still matches the first: no face morphing, extra limbs, outfit or prop changes, new people, or sudden light changes.
4. A failing **image**: redo it in Flow with the same prompt from `flow/README.md` and the same references, adding one short correction line (for example "Thatha wears no shawl"). Try up to 3 times; if it still fails, mark it with the problem and tell the user.
5. A failing **clip** costs credits to redo. Redo it only if today's credits allow, otherwise leave it marked with the problem and tell the user, who decides.
6. Record the verdicts in `continuity_review.json`: `"pass"` for a good shot, otherwise a short description of what is wrong. `studio.py assemble` refuses to render until every image and every clip is `"pass"`.

```json
{"images": {"1": "pass", "2": "pass", "7": "Thatha has a shawl; outfit says none"},
 "clips":  {"1": "pass", "4": "puppy's ear flips to the right side mid-clip"}}
```

7. If something on the character sheet or in a recurring place reference itself looks wrong, don't fix it per shot: tell the user, because changing a reference affects every future episode.

## Redoing without duplicates

Before redoing an image or clip, search the Flow project for its `flow_name` (from `episodes/<id>/flow/jobs.json`) and for tiles titled with its prompt. If a download failed or the tool reported an error, Flow often finished the job anyway: download that result instead of generating again. Name every new generation with its `flow_name`, plus `_v2` or `_v3` for deliberate redos.
