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
