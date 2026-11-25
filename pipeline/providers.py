"""One function per external model.

Stages never talk to an API directly: they call these functions, which go
through call_model() and so are always retried and logged.
"""

import base64

import requests
from google import genai

from .common import call_model, require_env

TEXT_MODEL = "gemini-3.8-flash"
TTS_MODEL = "gemini-3.8-flash-tts"
IMAGE_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"

_gemini = None


def gemini_client():
    """Create the Gemini client once and reuse it."""
    global _gemini
    if _gemini is None:
        _gemini = genai.Client(api_key=require_env("GEMINI_API_KEY"))
    return _gemini


def _usage(interaction):
    usage = getattr(interaction, "usage", None)
    return {"usage": usage.model_dump(exclude_none=True)} if usage is not None else {}


def gemini_text(prompt, *, stage, model=TEXT_MODEL, shot=None):
    """Text in, text out (script, storyboard drafts, translation)."""
    def fn():
        interaction = gemini_client().interactions.create(model=model, input=prompt, timeout=90)
        return interaction.output_text, _usage(interaction)

    return call_model(stage=stage, provider="gemini", model=model,
                      params={"prompt": prompt}, fn=fn, shot=shot)


def gemini_tts(text, *, stage, voice="Sulafat", style="", model=TTS_MODEL, shot=None):
    """Text in, WAV bytes out (24 kHz, mono). style is a delivery note such as 'warm, unhurried'."""
    item = {"type": "text", "text": text}
    if style:
        item["annotations"] = [{"type": "speech_metadata", "style": style}]

    def fn():
        interaction = gemini_client().interactions.create(
            model=model,
            input=[{"type": "user_input", "content": [item]}],
            api_version="v1beta",
            timeout=90,
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": voice}]},
        )
        data = interaction.output_audio.data
        audio = base64.b64decode(data) if isinstance(data, str) else bytes(data)
        return audio, {"output_bytes": len(audio), **_usage(interaction)}

    return call_model(stage=stage, provider="gemini", model=model,
                      params={"text": text, "voice": voice, "style": style}, fn=fn, shot=shot)


def cloudflare_image(prompt, *, stage, width=1024, height=1024, seed=None,
                     references=(), model=IMAGE_MODEL, shot=None):
    """Text (+ up to 4 reference images) in, image bytes out, from Cloudflare Workers AI.

    references is a list of (name, png_bytes). The model uses them to keep a
    character or object looking the same across shots.
    """
    account = require_env("CLOUDFLARE_ACCOUNT_ID")
    token = require_env("CLOUDFLARE_API_TOKEN")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
    fields = {"prompt": prompt, "width": str(width), "height": str(height)}
    if seed is not None:
        fields["seed"] = str(seed)
    files = {k: (None, v) for k, v in fields.items()}
    for i, (name, data) in enumerate(list(references)[:4]):
        files[f"input_image_{i}"] = (name, data, "image/png")

    def fn():
        response = requests.post(url, headers={"Authorization": f"Bearer {token}"},
                                 files=files, timeout=120)
        if not response.ok:
            raise requests.HTTPError(f"{response.status_code}: {response.text[:300]}",
                                     response=response)
        body = response.json()
        b64 = (body.get("result") or body).get("image")
        if not b64:
            raise RuntimeError(f"No image in response: {str(body)[:300]}")
        image = base64.b64decode(b64)
        return image, {"output_bytes": len(image)}

    return call_model(stage=stage, provider="cloudflare", model=model,
                      params={"prompt": prompt, "width": width, "height": height,
                              "references": [name for name, _ in references]},
                      seed=seed, fn=fn, shot=shot)


def image_extension(data):
    """Pick the file extension from the image's first bytes."""
    if data.startswith(b"\x89PNG"):
        return ".png"
    if data.startswith(b"\xff\xd8"):
        return ".jpg"
    if data[8:12] == b"WEBP":
        return ".webp"
    return ".bin"
