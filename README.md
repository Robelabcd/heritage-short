# Heritage Short: Three Rounds

An 83-second film about leaving Addis Ababa to study abroad, told through the three rounds of an Ethiopian coffee ceremony (abol, tona, baraka). It is made by a pipeline that turns one written storyboard, `storyboard.json`, into a finished film in vertical (9:16) and horizontal (16:9), with AI keyframes, three AI video clips, an original score, narration and English subtitles.

Built for the AI-Content Generation challenge, November 2026.

## Quick start

Requires Python 3.10+ and an FFmpeg build with libass (we used `conda install -c conda-forge ffmpeg`). `make assemble` checks for every filter it needs before it starts.

    git clone https://github.com/Robelabcd/heritage-short.git
    cd heritage-short
    make setup
    cp .env.example .env

Put your keys in `.env`: `GEMINI_API_KEY`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`. Both have free tiers.

    make smoke
    make film

`make film` validates the storyboard, makes the narration and keyframes, and writes `outputs/film/film_9x16.mp4` and `film_16x9.mp4`. Everything already made is reused from the cache, so on a fresh clone it only rebuilds the edit.

## Commands

| Command | What it does |
|---|---|
| `make validate` | Checks `storyboard.json` against the schema and the story rules |
| `make narration` | One TTS file per line (Gemini 3.8 Flash TTS) |
| `make references` | 4 candidate reference images per character; pick one and set `style.reference_seeds` |
| `make keyframes` | One keyframe per shot, conditioned on the chosen references, plus a contact sheet |
| `make radio-cut` | Narration, subtitles and a placeholder chord over black, for an early user test |
| `make assemble` | The edit: clips or Ken Burns moves, ducked score, loudness -14 LUFS, subtitles, both formats |
| `make film` | validate, narration, keyframes, assemble |
| `make costs` | Rewrites `COSTS.md` from `runs.jsonl` |

The two GPU stages are Colab notebooks: `notebooks/music_acestep.ipynb` (ACE-Step 1.5) and `notebooks/video_wan.ipynb` (Wan 2.2). Their chosen outputs and run logs are committed, so `make film` needs no GPU.

## Cost

A clean run of the whole film is a few cents at list prices, and $0 on the free tiers. See `COSTS.md`, which is generated from the log of every model call.

## Documents

| File | What is in it |
|---|---|
| `DESIGN.md` | Audience, story, design choices, user tests |
| `ARCHITECTURE.md` | Stages, contracts, cache, what one change re-runs |
| `DECISIONS.md` | Every decision and why |
| `EXPERIMENTS.md` | What was tried and what it showed |
| `FAILURES.md` | What broke and how it was fixed |
| `COSTS.md` | Calls, latency, GPU time, list prices |
| `ETHICS.md` | Consent, licences, private data, labelling |

## License

Code: MIT. Model licences and output terms: see `ETHICS.md`.
