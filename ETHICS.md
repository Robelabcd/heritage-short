# Ethics

## Consent
Recorded before anything of these people was generated.

| Person | How they appear | Consent | Date |
|---|---|---|---|
| Robel Berhe (me) | Main character, illustrated from a written description (no photos uploaded). My story, narrated in first person by a stock TTS voice | Mine, as author | 2026-11-25 |
| My mother | Her hands at the coffee ceremony (face not shown); her one Amharic line on the phone, spoken by a stock TTS voice | Yes, by WhatsApp, after I explained the film and the exact line she says. Screenshot kept privately | 2026-11-25 |

No voice is cloned. No photo of a real person is sent to any model.

## Licences

| Model | Used for | Where it ran | Licence / terms | Outputs |
|---|---|---|---|---|
| Gemini 3.8 Flash TTS | Narration and the Amharic line (stock voices Achird, Sulafat) | Gemini API, free tier | Gemini API Additional Terms | Google does not claim ownership of generated content |
| FLUX.2 klein 4B | Character references and keyframes | Cloudflare Workers AI, free allocation | Apache 2.0 | Ours to use |
| ACE-Step 1.5 (XL turbo) | Original score | Colab, open weights | MIT | Model card allows commercial use of generated music |
| Wan 2.2 TI2V-5B | Image-to-video clips | Colab, open weights | Apache 2.0 | Ours to use |
| FFmpeg (conda-forge build) | Editing, mixing, subtitles | Local | LGPL | Tool only |

No music, footage or images from anyone else are in the film. Photos of Addis Ababa and of coffee ceremonies found online were only looked at, to write better prompts. They were never sent to a model, because their licences are unknown.

## Private data
- **Gemini (free tier):** under the unpaid terms, human reviewers may read inputs and outputs. Only the narration script went there: text I am publishing in the film anyway. No names, places beyond the city, photos or contact details.
- **Cloudflare Workers AI:** Cloudflare states it does not use Workers AI customer content to train models. Only written prompts and our own generated reference images were sent.
- **Colab:** the open-weight models ran on a rented GPU. The notebooks read the public storyboard from GitHub and write to my own Google Drive.
- **Kept out of every model:** my real photos, my mother's photo, her voice, the WhatsApp consent screenshot, and the API keys (`.env` is git-ignored).

## Labelling
- The film ends on an AI end card that names the tools used.
- The public post carries the platform's AI-generated label and says the visuals, voices and music are AI-generated.
- The story and the proverb are real. The images are illustrations, not documentary footage, and the narration says so in its own voice (first person, remembered).
