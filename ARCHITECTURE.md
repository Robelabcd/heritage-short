# Architecture

One file describes the film: `storyboard.json`. Every stage reads it, makes files under `outputs/`, and logs every model call to `runs.jsonl`. `make film` rebuilds the film from the storyboard. The two GPU stages run as Colab notebooks, and their outputs are committed.

## Pipeline

    storyboard.json
          |
          v
      validate            JSON Schema (shape) + Python checks (meaning)
          |
          +--> narration    Gemini 3.8 Flash TTS         -> outputs/narration/s01_0.wav ...
          |
          +--> references   FLUX.2 klein 4B (Cloudflare) -> 4 candidates per character
          |                 (a person picks one; the seed goes into style.reference_seeds)
          |
          +--> keyframes    FLUX.2 klein 4B + chosen references -> outputs/keyframes/s01.jpg ...
          |
          +--> music        Colab notebook, ACE-Step 1.5 -> outputs/music/score.wav
          |                 (3 candidates; a person picks one)
          |
          +--> clips        Colab notebook, Wan 2.2 TI2V-5B, image-to-video for 3 shots
          |                 -> outputs/clips/s07.mp4 ...
          v
      assemble (ffmpeg, local)
          segments  : clip if one exists, else a Ken Burns move on the keyframe
          picture   : concat segments + end card
          audio     : narration timeline + score, ducked under the voice, loudnorm -14 LUFS
          subtitles : from the storyboard's subtitle text, burned in
          -> outputs/film/film_9x16.mp4, film_16x9.mp4 (blurred pillarbox)

    every model call -> call_model() -> one line in runs.jsonl
    every stage      -> outputs/<stage>/manifest.json (output file -> input hash)
    make costs       -> COSTS.md, generated from runs.jsonl

## The three contracts

**1. The storyboard schema** (`schema/storyboard.schema.json` + `pipeline/validate.py`)
The schema checks shape: required fields, types, ranges (8-12 shots, 3-12 s each).
`validate.py` checks meaning: unique shot ids, known speakers and characters, a chosen reference for every character used, total length 60-90 s, and a warning when a line is too long for its shot (measured at 1.7 words per second).
Every stage runs `validate` first, so a bad storyboard fails before any paid call.

**2. One door to every model** (`call_model` in `pipeline/common.py`)
- A hard timeout of 120 s, in its own thread. The SDK timeout alone did not stop a hung call (FAILURES F04).
- Up to 3 attempts with backoff, retried only for errors that can succeed later: 429, 5xx, network errors and timeouts. A 400 or 404 fails at once.
- One line in `runs.jsonl` per attempt: stage, shot, provider, model, params, seed, status, latency, usage, error.

**3. The cache** (`StageCache` in `pipeline/common.py`)
Each output is stored with a hash of the inputs that made it. It is reused only if the file exists and the hash still matches.
- narration: model, voice, style, text
- keyframes: model, prompt, seed, size, and the hashes of the reference images used
- segments: source file hash, duration, motion

The hashes cascade: a new reference image changes every keyframe that uses it, and a new keyframe changes its segment.

## What happens when one line changes

Edit the narration text of one shot in `storyboard.json`, then run `make film`:
1. `validate` passes, and warns if the new line is too long for the shot.
2. `narration`: one hash changes, so there is **one** TTS call. The other lines are reused.
3. `keyframes`: no hash changes, so there are **zero** image calls.
4. `assemble`: the narration track, the mix and the subtitles rebuild locally with ffmpeg. Unchanged segments are reused.

`runs.jsonl` shows exactly one new model call. That is the walkthrough demo.

## Why the GPU stages are notebooks

The development machine is a MacBook Air with no CUDA GPU. Music and video run on Colab (an L4 GPU).
- Each notebook reads `storyboard.json` straight from GitHub, so it uses the same contract.
- It writes a `manifest.json` with input hashes and its own run log in the `runs.jsonl` format, so `make costs` can count it.
- The chosen outputs are committed, so `make film` on any machine rebuilds the same film without a GPU.

| Stage | Where | Typical time |
|---|---|---|
| narration | Gemini API | about 4 s per line |
| references | Cloudflare Workers AI | about 10 s per image |
| keyframes | Cloudflare Workers AI | about 7 s per image |
| music | Colab L4, 8 steps | about 5 s per 85 s score |
| clips | Colab L4, 40 steps, 704x1280, 121 frames | about 17 min per 5 s clip |
| assemble | local ffmpeg | about 5 s per step |

## Portability checks

- `assemble` checks first that ffmpeg has every filter it needs, and names any that are missing.
- It picks the H.264 encoder at run time: libx264, then h264_videotoolbox, then libopenh264. The conda-forge build has no libx264 (FAILURES F05, F06).
- API keys come only from `.env`, which is git-ignored. `.env.example` lists the names without values.
