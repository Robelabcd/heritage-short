# Heritage Short

A pipeline that turns one written storyboard (`storyboard.json`) into a
60–90 second short film: AI keyframes, moving shots, an original score,
narration and a finished edit, in vertical (9:16) and horizontal (16:9).

> **Status:** work in progress. Built for the AI-Content Generation
> challenge, November 2026.

## Setup

Requires Python 3.10+ and FFmpeg (`brew install ffmpeg` on macOS).

```bash
git clone https://github.com/Robelabcd/heritage-short.git
cd heritage-short
make setup
cp .env.example .env
```

Then put your API keys in `.env`.

## License

Code: MIT. Model licences and output terms: see `ETHICS.md`.
