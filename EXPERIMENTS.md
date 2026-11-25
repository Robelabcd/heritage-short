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
