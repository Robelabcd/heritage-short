"""Shared helpers for every stage: paths, secrets, the call log and retries.

Every model call in the project goes through call_model(), so every call is
timed, retried on temporary errors, and written as one line to runs.jsonl.
"""

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
RUNS_LOG = ROOT / "runs.jsonl"
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

load_dotenv(ROOT / ".env")


def require_env(name):
    """Read a secret from .env, or stop with a clear message."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing {name}. Copy .env.example to .env and fill it in.")
    return value


def log_call(record):
    """Append one JSON line to runs.jsonl."""
    record = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "run_id": RUN_ID, **record}
    with RUNS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _status_code(exc):
    """Find an HTTP status code on an exception, if it has one."""
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    value = getattr(getattr(exc, "response", None), "status_code", None)
    return value if isinstance(value, int) else None


def is_retryable(exc):
    """Retry rate limits (429), server errors (5xx) and network errors.
    Never retry bad requests or bad keys (other 4xx): they fail the same way again."""
    code = _status_code(exc)
    if code is None:
        return True
    return code == 429 or code >= 500


def run_with_timeout(fn, timeout_s):
    """Run fn() in a background thread and give up after timeout_s seconds.

    Our own deadline, independent of any SDK: if a request hangs, we raise
    TimeoutError (retryable) instead of waiting forever.
    """
    box = {}

    def target():
        try:
            box["value"] = fn()
        except Exception as exc:
            box["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive():
        raise TimeoutError(f"no response after {timeout_s}s")
    if "error" in box:
        raise box["error"]
    return box["value"]


def call_model(*, stage, provider, model, params, fn, shot=None, seed=None,
               cost_usd=0.0, max_attempts=3, base_delay=4.0, timeout_s=120):
    """Run fn() with retries and log every attempt.

    fn() must return (result, extra): result goes back to the caller, extra is a
    dict merged into the log line (for example token usage or output size).
    """
    base = {"stage": stage, "shot": shot, "provider": provider, "model": model,
            "params": params, "seed": seed}
    for attempt in range(1, max_attempts + 1):
        start = time.perf_counter()
        try:
            result, extra = run_with_timeout(fn, timeout_s)
        except Exception as exc:
            latency = round(time.perf_counter() - start, 3)
            log_call({**base, "attempt": attempt, "status": "error",
                      "latency_s": latency, "cost_usd": 0.0,
                      "error": f"{type(exc).__name__}: {exc}"[:500]})
            if attempt == max_attempts or not is_retryable(exc):
                raise
            delay = base_delay * 2 ** (attempt - 1)
            print(f"  {provider}/{model} failed (attempt {attempt}): {exc}. Retrying in {delay:.0f}s")
            time.sleep(delay)
        else:
            latency = round(time.perf_counter() - start, 3)
            log_call({**base, "attempt": attempt, "status": "ok",
                      "latency_s": latency, "cost_usd": cost_usd, **extra})
            return result


# ---------------------------------------------------------------------------
# Caching: regenerate an output only when the inputs that produced it change.
# ---------------------------------------------------------------------------

import hashlib
import subprocess


def input_hash(inputs):
    """A short fingerprint of everything that determines an output."""
    text = json.dumps(inputs, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class StageCache:
    """Remembers which inputs produced each output file of a stage.

    outputs/<stage>/manifest.json maps file name -> input hash. An output is
    reused only if the file exists AND its recorded hash matches the new inputs.
    """

    def __init__(self, stage):
        self.dir = OUTPUTS / stage
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "manifest.json"
        self.manifest = json.loads(self.path.read_text()) if self.path.exists() else {}

    def is_fresh(self, name, digest):
        return (self.dir / name).exists() and self.manifest.get(name) == digest

    def record(self, name, digest):
        self.manifest[name] = digest
        self.path.write_text(json.dumps(self.manifest, indent=2, sort_keys=True) + "\n")


def run_ffmpeg(args, *, stage, label):
    """Run ffmpeg (deterministic, not a model), stop on failure, log the timing."""
    start = time.perf_counter()
    result = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
                            cwd=ROOT, capture_output=True, text=True)
    latency = round(time.perf_counter() - start, 3)
    status = "ok" if result.returncode == 0 else "error"
    log_call({"stage": stage, "shot": None, "provider": "local", "model": "ffmpeg",
              "params": {"label": label}, "seed": None, "attempt": 1, "status": status,
              "latency_s": latency, "cost_usd": 0.0,
              **({"error": result.stderr[-500:]} if status == "error" else {})})
    if result.returncode != 0:
        raise SystemExit(f"ffmpeg failed ({label}):\n{result.stderr[-1500:]}")
    return result


def video_encoder_args():
    """Pick an H.264 encoder this ffmpeg actually has.

    Builds differ: Homebrew and most Linux builds include libx264, the conda-forge
    build does not (licensing) but has Apple's hardware encoder on macOS and
    OpenH264. Checking at run time keeps `make film` working on any machine.
    """
    listing = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                             capture_output=True, text=True).stdout
    options = [
        ("libx264", ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]),
        ("h264_videotoolbox", ["-c:v", "h264_videotoolbox", "-b:v", "8M"]),
        ("libopenh264", ["-c:v", "libopenh264", "-b:v", "8M"]),
    ]
    for name, args in options:
        if f" {name} " in listing:
            return args + ["-pix_fmt", "yuv420p"]
    raise SystemExit("ffmpeg has no H.264 encoder (need libx264, h264_videotoolbox or libopenh264)")
