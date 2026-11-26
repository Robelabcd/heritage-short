# Experiments

One change at a time, seed fixed where possible. Evidence = runs.jsonl entries or measured numbers.

<!-- Template
## E01: title (date, stage)
- **Hypothesis:**
- **Change:**
- **Result:**
- **Decision:**
-->

## E01: Does the image model know what a jebena is? (2026-11-25, keyframes)
- **Hypothesis:** Naming the object ("a traditional Ethiopian clay coffee pot") is enough for FLUX.2 klein to draw a jebena.
- **Change:** Smoke test prompt named the object only (seed 42, 512x512).
- **Result:** It drew a Western-style terracotta jug with a wide mouth (outputs/smoke/image.jpg). The model does not know the object by name.
- **Decision:** Describe the shape instead (round belly, long narrow neck, short spout, handle from neck to body, black clay) and store it once in `style.characters.jebena`, so every shot that shows it uses the same description. To be verified in the keyframe stage.
- **E01 result:** With the shape described, all 4 jebena reference candidates showed a round-bellied black clay pot with a long neck, spout, handle and straw ring. Description works where the name does not.

## E02: A two-view reference sheet produces two people (2026-11-25, keyframes)
- **Hypothesis:** A reference sheet showing the character from the front and in three-quarter view gives the model more identity information.
- **Change:** v1 references were two-view sheets; keyframes were conditioned on them.
- **Result:** s03, s06 and s07 each showed two copies of me side by side. The model copied the sheet's layout, not just the face.
- **Decision:** References are one single three-quarter view. In v2, every shot that shows me shows exactly one of me.

## E03: My first Addis prompt encoded a stereotype (2026-11-25, keyframes)
- **Hypothesis:** "a hillside, low houses with tin roofs" describes Addis Ababa.
- **Change:** v1 used that wording.
- **Result:** The model drew a poor rural village. My own review: it looks nothing like my city.
- **Decision:** Describe the city as it is: the view from Entoto, eucalyptus, palm-lined boulevards, glass high-rises, blue-and-white minibuses. v2 s01 is a recognisable modern capital. Lesson: the model amplifies whatever the prompt implies, so a cultural insider has to review the prompts.

## E04: Without details, the model drew a Western coffee break (2026-11-25, keyframes)
- **Hypothesis:** "a coffee ceremony" is enough context.
- **Change:** v1 s03 and s09 named the ceremony but not its objects.
- **Result:** Tables, mugs, metal coffee pots and paper cups. My comment: "we don't drink coffee like that."
- **Decision:** Describe the objects and the posture: low stools and the floor, fresh grass, a rekebot tray with small handleless cups, the jebena on a straw ring by a charcoal brazier, incense, popcorn. v2 s03 shows the real ceremony.

## E05: A single-person reference erases the group (2026-11-25, keyframes)
- **Hypothesis:** Conditioning every shot I appear in on my reference keeps me consistent.
- **Change:** v2 s09 (me pouring coffee for four friends) used my reference.
- **Result:** Only I appeared, standing alone in a living room. The reference outweighed "five students in a circle".
- **Decision:** No identity reference for wide group shots; describe me in words (hair, olive-green hoodie). In a wide shot the clothes carry the identity.

## E06: Score level under the narration (2026-11-25, assembly)
- **Hypothesis:** Sidechain ducking alone keeps the ACE-Step score under the voice.
- **Change:** Measured mean level during speech and during the pauses between lines (real narration, chosen score), at three score levels before ducking.
- **Result:** 0 dB: speech -18.6 dB, pauses -14.5 dB, so the music swelled 4.1 dB louder than the voice between lines. -8 dB: pauses 1.8 dB below speech. -12 dB: pauses 5.2 dB below speech. The ACE-Step track is mastered loud (-12.5 LUFS) and ducking only acts while the voice is present.
- **Decision:** `music.gain_db = -12` in the storyboard (a creative setting, so it lives in the contract) plus ducking. Final loudness ceiling lowered to -1.5 dB true peak; measured peak -1.5 dB, inside the brief's -1 dB limit.

## E07: Choosing the score among 3 ACE-Step candidates (2026-11-25, music)
- **Hypothesis:** Of three seeds with the same caption and bpm, the calmest one will sit best under the narration.
- **Change:** Generated seeds 1-3 on a Colab L4 (about 4 s per 85 s track, logged in runs.jsonl), listened to each against the film.
- **Result:** I chose seed 2 because it feels calmer and leaves room for the voice. Measured for comparison: loudness -14.2 / -12.5 / -11.6 LUFS and loudness range 4.7 / 3.5 / 2.6 LU for seeds 1 / 2 / 3. Seed 2 is not the quietest, and simple measures of busyness did not separate the candidates clearly, so the choice rests on listening, not on level.
- **Decision:** Seed 2. Its level is set by `music.gain_db` (E06), not by the candidate.

## E08: Clothing drift on s10 (accepted)

- **Question:** can reseeding alone keep Robel's olive-green hoodie in the final shot?
- **Tried:** seeds 110, 210, 310 with the same prompt and the same reference image.
- **Result:** the reference sets the face and hair well, but the clothes still drift toward a white T-shirt in some seeds.
- **Decision:** accepted seed 310 and stopped at three attempts. More seeds cost time for a detail that doesn't change the story.
- **Would try next:** put the clothing first in the shot prompt, or use a reference image cropped to the torso.

## E09: Animate only the three emotional peaks (2026-11-25, clips)
- **Hypothesis:** Wan 2.2 TI2V-5B can animate the keyframes at full vertical resolution on a Colab L4 without losing identity, if motion prompts stay small and the negative prompt targets faces and hands.
- **Change:** Image-to-video for s03 (the ceremony), s07 (the midnight call) and s09 (coffee with new friends): 704x1280, 121 frames (5 s at 24 fps), 40 steps, guidance 5.0, model CPU offload and VAE tiling. All other shots keep Ken Burns moves on their keyframes.
- **Result:** 3/3 succeeded on the first attempt: 21.1, 20.5 and 20.5 min (62 GPU min). About 17 min of each is diffusion (25 s per step); the rest is decoding and saving. Identity held: in s07 the face stays in frame for the whole proverb. The 5 s clips are slowed by up to 1.6x and hold their last frame to fill 8-10 s shots.
- **Decision:** Motion only where the story peaks. Animating all 10 shots would cost about 3.5 GPU hours per full run; three clips gave the film movement at its three emotional beats for about one hour.

## E10: Make one memory specific (2026-11-25, narration, from user test 1)
- **Hypothesis:** Replacing a general phrase with real sensory details makes the ceremony easier to picture, without changing the film's length.
- **Change:** s03 "And between them, we talk about everything." became "Between them: incense, gossip, and my mother's TV drama." (three details from my family's ceremonies).
- **Result:** `make validate` estimated 8.2 s at 1.7 words per second and passed, but the real audio ran 1.0 s past the shot: the colon and commas add pauses that a word count does not see. `make assemble` measures the real audio and warned. Cut to "Incense, gossip, and my mother's TV drama.", which fits. Two TTS calls in total, zero image or video calls.
- **Decision:** Keep the shorter line. The word-rate check is an early estimate only; the measured check at assembly is the one that counts, so both stay. Test 2 checks whether the memory now feels vivid.

## E11: Teaching the model what a jebena is (2026-11-26, references, from user test 2; follows E01)
- **Hypothesis:** A precise written description of a real jebena, used to make a new reference image, fixes the teapot in every jebena shot at once.
- **Change:** A tester said the jebena "doesn't look like jebena". I described a real one from a photo, in words only: the photo's licence is unknown, so it was never sent to a model. Then three rounds of 4 reference candidates.
- **Result:** Round 1 (black glaze, tibeb bands, a stopper): the right materials, but a short wide neck, still a teapot. Round 2 (proportions: "the neck as tall as the belly, about two fingers wide"): the right neck, but the spout disappeared. Round 3 (the spout named first): seed 4 had the neck, the spout, the bands and the straw ring. Fixing one feature tended to drop another; what the description named first survived.
- **Decision:** `reference_seeds.jebena = 4`. Each keyframe's hash includes its reference image, so one change regenerated exactly the four jebena keyframes (s03, s04, s08, s09) and nothing else: 12 reference calls and 4 keyframe calls. The s09 Wan clip still shows the old jebena.
