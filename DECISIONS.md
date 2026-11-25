# Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-11-25 | Public repo `Robelabcd/heritage-short`, MIT | Graders and viewers can clone it; secrets kept out via .gitignore |
| 2026-11-25 | Makefile as the single entry point (`make film`) | One documented command runs the pipeline from a clean clone |
| 2026-11-25 | `runs.jsonl` and `outputs/` committed | The log is graded evidence; outputs let anyone inspect a run |
| 2026-11-25 | Every model call goes through one function (`call_model`) | Guarantees a complete log, uniform retries, one place to change a provider |
| 2026-11-25 | Story: my move from Addis Ababa, structured as the three coffee rounds | A personal story with a built-in motif and a clear three-act shape |
| 2026-11-25 | English narration, one Amharic line from my mother | Reaches students from any country; keeps the heritage; subtitled |
| 2026-11-25 | Colab Pro as main GPU, Kaggle as backup | Faster GPUs than Kaggle's free T4 for Wan 2.2; cost recorded in COSTS.md |
| 2026-11-25 | Claude (claude.ai) as coding agent; I design and review | Stated honestly; every script explained before it was created |
| 2026-11-25 | Storyboard checked in two layers: JSON Schema for shape, Python for meaning | A schema cannot express cross-field rules (unique ids, speakers with voices, total length, narration fitting its shot) |
| 2026-11-25 | Narration fit checked at a measured 1.7 words/s | Measured from the smoke test (8 words in 4.8 s with the "unhurried" style), slower than the brief's 2-2.5 estimate |
| 2026-11-25 | Recurring subjects (me, the jebena) described once in `style.characters` | One fixed description per subject keeps shots consistent; applies the E01 fix everywhere |
| 2026-11-25 | Narrator voice Achird (male), mother's line Sulafat (female) | The narrator is me; the smoke test had used a female voice by mistake |
| 2026-11-25 | Primary format 9:16 | My audience watches on phones in vertical feeds |
