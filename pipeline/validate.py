"""Validate storyboard.json before any stage runs.

Two layers of checks:
1. Shape: the JSON Schema in schema/storyboard.schema.json (types, required fields, enums).
2. Meaning: rules a schema cannot express (unique ids, references, total length,
   narration that fits its shot).

Run with: make validate
Stages call load_storyboard(), so a broken storyboard stops the pipeline before
any model is called.
"""

import json

from jsonschema import Draft202012Validator

from .common import ROOT

SCHEMA_PATH = ROOT / "schema" / "storyboard.schema.json"
STORYBOARD_PATH = ROOT / "storyboard.json"
FILM_MIN_S, FILM_MAX_S = 60, 90


def check(storyboard):
    """Return (errors, warnings) as two lists of strings."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}"
              for e in Draft202012Validator(schema).iter_errors(storyboard)]
    if errors:
        return errors, []

    warnings = []
    shots = storyboard["shots"]
    ids = [s["id"] for s in shots]
    if len(ids) != len(set(ids)):
        errors.append(f"shot ids are not unique: {ids}")

    characters = storyboard["style"]["characters"]
    voices = storyboard["voices"]
    for shot in shots:
        for name in shot["characters"]:
            if name not in characters:
                errors.append(f"{shot['id']}: unknown character '{name}'")
        for line in shot["lines"]:
            if line["speaker"] not in voices:
                errors.append(f"{shot['id']}: unknown speaker '{line['speaker']}'")

    for cue in storyboard["music"]["cues"]:
        for key in ("from_shot", "to_shot"):
            if cue[key] not in ids:
                errors.append(f"music cue refers to unknown shot '{cue[key]}'")

    total = sum(s["duration_s"] for s in shots) + storyboard["end_card"]["duration_s"]
    if not FILM_MIN_S <= total <= FILM_MAX_S:
        errors.append(f"film length {total:.1f}s is outside {FILM_MIN_S}-{FILM_MAX_S}s")

    rate = storyboard["format"]["words_per_second"]
    for shot in shots:
        words = sum(len(line["text"].split()) for line in shot["lines"])
        needed = words / rate
        if needed > shot["duration_s"]:
            warnings.append(f"{shot['id']}: {words} words need ~{needed:.1f}s "
                            f"but the shot is {shot['duration_s']}s")
    return errors, warnings


def load_storyboard():
    """Load and validate the storyboard, or stop with a clear list of problems."""
    storyboard = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    errors, warnings = check(storyboard)
    for w in warnings:
        print(f"WARNING  {w}")
    if errors:
        raise SystemExit("storyboard.json is invalid:\n  " + "\n  ".join(errors))
    return storyboard


def main():
    storyboard = load_storyboard()
    shots = storyboard["shots"]
    rate = storyboard["format"]["words_per_second"]
    print(f"{'shot':<5}{'act':<5}{'secs':>5}{'words':>7}{'~speech':>9}  size")
    for s in shots:
        words = sum(len(line["text"].split()) for line in s["lines"])
        print(f"{s['id']:<5}{s['act']:<5}{s['duration_s']:>5}{words:>7}{words / rate:>8.1f}s  {s['shot_size']}")
    total = sum(s["duration_s"] for s in shots) + storyboard["end_card"]["duration_s"]
    print(f"\nOK: {len(shots)} shots, {total:.0f}s including the end card.")


if __name__ == "__main__":
    main()
