"""Build COSTS.md from runs.jsonl.

  make costs   reads every logged call, prices it at public list prices, and
               rewrites the generated part of COSTS.md (between the markers).
               Anything you write outside the markers is kept.

We paid $0 for the APIs (free tiers), so "cost" here means two things:
  measured   calls, errors, latency and GPU minutes, straight from the log
  list price what the same calls would cost on a paid plan, from usage
             (tokens, image tiles, audio seconds, GPU minutes)
Failed calls are counted but priced at $0, because failed requests are not billed.
"""
import json
import math
from collections import defaultdict

from pipeline.common import OUTPUTS, ROOT, RUNS_LOG

COSTS_MD = ROOT / "COSTS.md"
START, END = "<!-- costs:start -->", "<!-- costs:end -->"

COLAB_USD_PER_UNIT = 9.99 / 100
COLAB_UNITS_PER_HOUR = {"NVIDIA L4": 2.33, "NVIDIA A100": 15.0}
CF_FREE_NEURONS_PER_DAY = 10_000
TILE = 512

PRICES = [
    ("Gemini 3.8 Flash TTS", "$0.50 / 1M text tokens in, $9.00 / 1M audio tokens out",
     "https://ai.google.dev/gemini-api/docs/pricing"),
    ("Gemini 3.8 Flash", "$0.75 / 1M tokens in, $3.75 / 1M tokens out",
     "https://ai.google.dev/gemini-api/docs/pricing"),
    ("FLUX.2 klein 4B (Cloudflare)", "$0.000287 per output 512x512 tile, $0.000059 per input tile "
     "(26.05 / 5.37 neurons); 10,000 neurons free per day",
     "https://developers.cloudflare.com/workers-ai/platform/pricing/"),
    ("ACE-Step (hosted equivalent)", "$0.0003 per second of generated audio",
     "https://fal.ai/models/fal-ai/ace-step"),
    ("Colab Pro compute units", "$9.99 per 100 units; L4 about 2.33 units/hour (observed), "
     "A100 about 15 units/hour", "https://colab.research.google.com/signup"),
]


def load_runs():
    if not RUNS_LOG.exists():
        raise SystemExit("runs.jsonl not found: run a stage first")
    return [json.loads(line) for line in RUNS_LOG.read_text().splitlines() if line.strip()]


def tiles(width, height):
    return math.ceil(width / TILE) * math.ceil(height / TILE)


def gpu_name(provider):
    """'colab (NVIDIA L4)' -> 'NVIDIA L4'."""
    return provider[provider.find("(") + 1:provider.rfind(")")] if "(" in provider else provider


def token_counts(usage):
    """(text tokens in, audio tokens out, text tokens out) from a Gemini usage block."""
    usage = usage or {}
    text_in = sum(m["tokens"] for m in usage.get("input_tokens_by_modality", [])
                  if m.get("modality") == "text")
    out = usage.get("output_tokens_by_modality", [])
    audio_out = sum(m["tokens"] for m in out if m.get("modality") == "audio")
    text_out = sum(m["tokens"] for m in out if m.get("modality") == "text")
    if not out:
        text_out = usage.get("total_output_tokens", 0)
    return text_in, audio_out, text_out


def price(row):
    """List-price equivalent in USD and Cloudflare neurons for one logged call."""
    if row.get("status") != "ok":
        return 0.0, 0.0
    model, params = row["model"], row.get("params", {})
    if row["provider"] == "local":
        return 0.0, 0.0
    if model.endswith("-tts"):
        text_in, audio_out, _ = token_counts(row.get("usage"))
        return text_in * 0.50e-6 + audio_out * 9.00e-6, 0.0
    if model.startswith("gemini"):
        text_in, _, text_out = token_counts(row.get("usage"))
        return text_in * 0.75e-6 + text_out * 3.75e-6, 0.0
    if "flux-2-klein-4b" in model:
        out_tiles = tiles(params.get("width", 1024), params.get("height", 1024))
        in_tiles = len(params.get("references", []))
        usd = out_tiles * 0.000287 + in_tiles * 0.000059
        return usd, out_tiles * 26.05 + in_tiles * 5.37
    if row["provider"].startswith("colab"):
        hours = row.get("gpu_minutes", 0.0) / 60
        units = hours * COLAB_UNITS_PER_HOUR.get(gpu_name(row["provider"]), 2.33)
        return units * COLAB_USD_PER_UNIT, 0.0
    return 0.0, 0.0


def hosted_music_equivalent(row):
    if row.get("stage") != "music" or row.get("status") != "ok":
        return 0.0
    return row.get("params", {}).get("audio_duration", 0) * 0.0003


def summarise(rows):
    groups = defaultdict(lambda: {"calls": 0, "ok": 0, "errors": 0, "retries": 0,
                                  "latency": 0.0, "ok_latency": 0.0, "gpu_min": 0.0,
                                  "usd": 0.0, "neurons": 0.0})
    for row in rows:
        g = groups[(row["stage"], row["provider"], row["model"])]
        usd, neurons = price(row)
        ok = row.get("status") == "ok"
        g["calls"] += 1
        g["ok" if ok else "errors"] += 1
        g["retries"] += row.get("attempt", 1) > 1
        g["latency"] += row.get("latency_s", 0.0)
        g["ok_latency"] += row.get("latency_s", 0.0) if ok else 0.0
        g["gpu_min"] += row.get("gpu_minutes", 0.0)
        g["usd"] += usd
        g["neurons"] += neurons
    return groups


def mean_ok_cost(rows, stage):
    costs = [price(r)[0] for r in rows if r["stage"] == stage and r.get("status") == "ok"]
    return sum(costs) / len(costs) if costs else 0.0


def clean_run(rows):
    """What one fresh `make film` (plus the two notebooks) would call, from the storyboard."""
    storyboard = json.loads((ROOT / "storyboard.json").read_text())
    clips_manifest = OUTPUTS / "clips" / "manifest.json"
    n_clips = len(json.loads(clips_manifest.read_text())) if clips_manifest.exists() else 0
    plan = [
        ("narration", sum(len(s["lines"]) for s in storyboard["shots"]), "one per narration line"),
        ("references", len(storyboard["style"]["characters"]) * 4, "4 candidates per character"),
        ("keyframes", len(storyboard["shots"]), "one per shot"),
        ("music", 3, "3 candidate scores (seeds 1-3)"),
        ("clips", n_clips, "image-to-video shots"),
    ]
    return [(stage, n, why, mean_ok_cost(rows, stage)) for stage, n, why in plan]


def neurons_by_day(rows):
    days = defaultdict(float)
    for row in rows:
        days[row["ts"][:10]] += price(row)[1]
    return {d: n for d, n in sorted(days.items()) if n}


def money(x):
    return f"${x:.4f}" if x < 1 else f"${x:.2f}"


def render(rows):
    groups = summarise(rows)
    total = {k: sum(g[k] for g in groups.values())
             for k in ("calls", "ok", "errors", "retries", "latency", "gpu_min", "usd")}
    hosted_music = sum(hosted_music_equivalent(r) for r in rows)
    out = [START, "",
           f"_Generated by `make costs` from {len(rows)} lines of runs.jsonl (last call {max(r['ts'] for r in rows)[:16].replace('T', ' ')} UTC). "
           "Do not edit between the markers; it is rewritten each time._", "",
           "## Summary", "",
           "| | |", "|---|---|",
           f"| Logged calls | {total['calls']} ({total['ok']} ok, {total['errors']} errors, "
           f"{total['retries']} retries) |",
           f"| Total wall time in calls | {total['latency'] / 60:.1f} min |",
           f"| GPU minutes (Colab, inference only) | {total['gpu_min']:.1f} |",
           f"| List-price equivalent of everything we ran | {money(total['usd'])} |",
           "| Cash spent | $0 on APIs (Gemini and Cloudflare free tiers); GPU time from an existing Colab Pro plan |", "",
           "## By stage", "",
           "| Stage | Provider | Model | Calls | OK | Errors | Total s | Mean s (ok) "
           "| GPU min | List-price equiv. |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for (stage, provider, model), g in sorted(groups.items()):
        mean = g["ok_latency"] / g["ok"] if g["ok"] else 0.0
        out.append(f"| {stage} | {provider} | `{model}` | {g['calls']} | {g['ok']} | {g['errors']} "
                   f"| {g['latency']:.1f} | {mean:.1f} | {g['gpu_min']:.2f} | {money(g['usd'])} |")

    plan = clean_run(rows)
    per_film = sum(n * each for _, n, _, each in plan)
    out += ["", "## One clean run of the film", "",
            "What a fresh run from storyboard.json would call, priced at the mean cost of the "
            "successful calls we logged for that stage.", "",
            "| Stage | Calls | Why | Each | Total |", "|---|---|---|---|---|"]
    for stage, n, why, each in plan:
        out.append(f"| {stage} | {n} | {why} | {money(each)} | {money(n * each)} |")
    out += [f"| **Film** | | | | **{money(per_film)}** |", "",
            f"Development cost {money(total['usd'])}, about "
            f"{total['usd'] / per_film:.1f}x one clean run: the difference is iteration "
            "(reference rounds, keyframe re-prompts, retries)." if per_film else "",
            "Thanks to the input-hash cache, changing one narration line re-runs one TTS call "
            f"(about {money(plan[0][3])}) and the local ffmpeg steps, nothing else."]

    out += ["", "## Free-tier usage", "",
            f"Cloudflare Workers AI gives {CF_FREE_NEURONS_PER_DAY:,} neurons per day.", "",
            "| Day (UTC) | Neurons used | Share of free allocation |", "|---|---|---|"]
    for day, n in neurons_by_day(rows).items():
        out.append(f"| {day} | {n:,.0f} | {n / CF_FREE_NEURONS_PER_DAY:.0%} |")
    if hosted_music:
        out += ["", f"Music ran on Colab. The same {sum(1 for r in rows if r['stage'] == 'music' and r.get('status') == 'ok')} "
                f"scores on a hosted ACE-Step API would cost about {money(hosted_music)}."]

    out += ["", "## Prices and assumptions", "",
            "| Item | List price | Source |", "|---|---|---|"]
    out += [f"| {name} | {p} | {url} |" for name, p, url in PRICES]
    out += ["",
            "- Failed calls (503, timeouts) are counted but priced at $0: they are not billed.",
            "- Cloudflare tiles: output tiles = ceil(w/512) x ceil(h/512); each reference image is "
            "sent at 512 px, so it counts as one input tile.",
            "- GPU minutes are inference time only. Colab bills connected runtime (model download, "
            "loading, idle), so the real unit use is higher: see the notes below.",
            "- Local ffmpeg steps cost nothing and are listed for timing only.", "", END]
    return "\n".join(out)


def main():
    generated = render(load_runs())
    text = COSTS_MD.read_text() if COSTS_MD.exists() else ""
    if START in text and END in text:
        before, rest = text.split(START, 1)
        after = rest.split(END, 1)[1]
        text = before + generated + after
    else:
        text = ("# Costs\n\n" + generated + "\n\n## Notes (hand-written)\n\n"
                "- Colab compute units before the GPU work: 107.\n")
    COSTS_MD.write_text(text)
    print(f"wrote {COSTS_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
