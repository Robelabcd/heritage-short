"""Step 1 smoke test: call each provider once, save what comes back, log every call.

Run with: make smoke
"""

from .common import OUTPUTS
from .providers import cloudflare_image, gemini_text, gemini_tts, image_extension

OUT = OUTPUTS / "smoke"


def check_text():
    text = gemini_text("In one sentence, what is the Ethiopian coffee ceremony?", stage="smoke")
    (OUT / "text.txt").write_text(text, encoding="utf-8")
    return text.strip()[:80]


def check_tts_english():
    audio = gemini_tts("In Addis Ababa, nobody drinks coffee alone.",
                       stage="smoke", style="warm, calm, unhurried")
    (OUT / "tts_en.wav").write_bytes(audio)
    return f"{len(audio):,} bytes"


def check_tts_amharic():
    audio = gemini_tts("ለሰው መድኃኒቱ ሰው ነው።", stage="smoke",
                       style="warm and gentle, like a mother comforting her son")
    (OUT / "tts_am.wav").write_bytes(audio)
    return f"{len(audio):,} bytes"


def check_image():
    image = cloudflare_image(
        "A traditional Ethiopian clay coffee pot on a woven mat, warm morning light, "
        "hand-painted gouache illustration",
        stage="smoke", width=512, height=512, seed=42)
    path = OUT / f"image{image_extension(image)}"
    path.write_bytes(image)
    return path.name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    failed = False
    for name, check in [("Gemini text", check_text), ("Gemini TTS (English)", check_tts_english),
                        ("Gemini TTS (Amharic)", check_tts_amharic), ("Cloudflare image", check_image)]:
        try:
            print(f"OK    {name}: {check()}")
        except Exception as exc:
            failed = True
            print(f"FAIL  {name}: {type(exc).__name__}: {exc}")
    print("\nEvery call is logged in runs.jsonl. Listen to outputs/smoke/*.wav and open the image.")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
