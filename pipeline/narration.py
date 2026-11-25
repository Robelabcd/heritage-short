"""Stage: narration. One WAV per spoken line, from storyboard.json.

Each line is cached by a hash of (model, voice, style, text). Change one line in
the storyboard and only that line is sent to the TTS model again.

Run with: make narration
"""

from .common import StageCache, input_hash
from .providers import TTS_MODEL, gemini_tts
from .validate import load_storyboard

STAGE = "narration"


def line_file(shot_id, index):
    return f"{shot_id}_{index}.wav"


def main():
    storyboard = load_storyboard()
    cache = StageCache(STAGE)
    made = reused = 0
    for shot in storyboard["shots"]:
        for i, line in enumerate(shot["lines"]):
            voice = storyboard["voices"][line["speaker"]]
            inputs = {"model": TTS_MODEL, "voice": voice["voice"],
                      "style": voice["style"], "text": line["text"]}
            name, digest = line_file(shot["id"], i), input_hash(inputs)
            if cache.is_fresh(name, digest):
                reused += 1
                continue
            audio = gemini_tts(line["text"], stage=STAGE, shot=shot["id"],
                               voice=voice["voice"], style=voice["style"])
            (cache.dir / name).write_bytes(audio)
            cache.record(name, digest)
            made += 1
            print(f"made    {name}  ({line['speaker']}: {line['text'][:50]})")
    print(f"\nnarration: {made} generated, {reused} reused from cache")


if __name__ == "__main__":
    main()
