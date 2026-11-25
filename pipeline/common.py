"""Shared helpers for every stage: paths, secrets, the call log and retries.

Every model call in the project goes through call_model(), so every call is
timed, retried on temporary errors, and written as one line to runs.jsonl.
"""

import json
import os
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


def call_model(*, stage, provider, model, params, fn, shot=None, seed=None,
               cost_usd=0.0, max_attempts=3, base_delay=4.0):
    """Run fn() with retries and log every attempt.

    fn() must return (result, extra): result goes back to the caller, extra is a
    dict merged into the log line (for example token usage or output size).
    """
    base = {"stage": stage, "shot": shot, "provider": provider, "model": model,
            "params": params, "seed": seed}
    for attempt in range(1, max_attempts + 1):
        start = time.perf_counter()
        try:
            result, extra = fn()
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
