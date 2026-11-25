# Failures

<!-- Template
## F01: title (date, stage)
- **What broke:**
- **What I tried:**
- **What fixed it / workaround:**
-->

## F01: Homebrew tried to compile FFmpeg from source (2026-11-25, setup)
- **What broke:** `brew install ffmpeg` warned that my Command Line Tools were outdated and started building every dependency from source (it was compiling openssl). FFmpeg has dozens of dependencies, so this would have taken hours.
- **What I tried:** Stopped the build with Ctrl+C rather than updating Xcode tools under time pressure.
- **What fixed it / workaround:** Installed a prebuilt FFmpeg from conda-forge into its own environment (`conda create -n ffmpeg -c conda-forge ffmpeg`) and symlinked `ffmpeg`/`ffprobe` into the project's `.venv/bin`. Verified it has the filters the pipeline needs: subtitles, sidechaincompress, loudnorm, zoompan.

## F02: Gemini text model overloaded, then a call hung (2026-11-25, smoke test)
- **What broke:** `gemini-3.8-flash` returned 503 "high demand… usually temporary" on all 3 attempts. On the next run a request hung with no response, because the Gemini calls had no timeout.
- **What I tried:** The retry logic worked as designed (waited 4 s, then 8 s; every attempt logged in runs.jsonl), but a 12-second backoff was shorter than the outage. Stopped the hung run with Ctrl+C.
- **What fixed it / workaround:** Added `timeout=90` to both Gemini calls, so a stuck request raises an error that `call_model` retries and logs instead of freezing. The text model is the least critical provider (the storyboard is written by hand), so I tested the other providers on their own and will retest text when load drops.

## F03: TTS model "not found" (404) (2026-11-25, smoke test)
- **What broke:** `gemini-3.8-flash-tts` returned 404 "not found… set the API version to v1beta", while the text model on the same key was reachable.
- **What I tried:** Read the error rather than changing the model name: it said the model only exists on the newer API version.
- **What fixed it / workaround:** Added `api_version="v1beta"` to the TTS call only (one line, smallest safe change). Both English and Amharic TTS then succeeded.

## F04: TTS request hung despite timeout=90 (2026-11-25, narration)
- **What broke:** During the narration stage, one TTS request never returned and printed nothing. The SDK's own `timeout=90` argument did not fire.
- **What I tried:** Stopped it with Ctrl+C. The 6 lines already made were cached, so nothing was lost.
- **What fixed it / workaround:** Added our own deadline in `call_model` (`run_with_timeout`): the call runs in a daemon thread and raises `TimeoutError` after 120 s, which is retried and logged. It no longer depends on any SDK honouring its timeout. Re-run: 5 generated, 6 reused from cache.

## F05: FFmpeg had no libx264 encoder (2026-11-25, radio cut)
- **What broke:** The render failed with `Unknown encoder 'libx264'`. The conda-forge FFmpeg build leaves out the GPL-licensed x264.
- **What I tried:** Listed the encoders the build does have.
- **What fixed it / workaround:** `video_encoder_args()` picks the first available H.264 encoder at run time (libx264, then Apple's h264_videotoolbox, then OpenH264), so the pipeline runs on any machine.
