"""Timeline: where every shot and every spoken line sits in the film, in seconds.

Pure arithmetic from the storyboard plus the measured length of each narration
WAV. Used by the radio cut now and by the final assembly later, so both agree.
"""

import subprocess
import textwrap

from .common import OUTPUTS, ROOT
from .narration import line_file

SAMPLE_RATE = 24000          # narration is converted to 24 kHz mono 16-bit
BYTES_PER_SECOND = SAMPLE_RATE * 2
LEAD_IN_S = 0.4              # pause after a cut before the narrator speaks
GAP_S = 0.35                 # pause between two lines in the same shot


def read_pcm(path):
    """Decode any audio file to raw 24 kHz mono 16-bit samples."""
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-f", "s16le", "-ac", "1", "-ar", str(SAMPLE_RATE), "-"],
        cwd=ROOT, capture_output=True, check=True).stdout


def build(storyboard):
    """Return (shots, lines, total_s, warnings) with start times in seconds."""
    shots, lines, warnings = [], [], []
    t = 0.0
    for shot in storyboard["shots"]:
        start, end = t, t + shot["duration_s"]
        shots.append({"id": shot["id"], "start": start, "end": end})
        cursor = start + LEAD_IN_S
        for i, line in enumerate(shot["lines"]):
            path = OUTPUTS / "narration" / line_file(shot["id"], i)
            pcm = read_pcm(path)
            length = len(pcm) / BYTES_PER_SECOND
            lines.append({"shot": shot["id"], "start": cursor, "end": cursor + length,
                          "pcm": pcm, "subtitle": line["subtitle"]})
            cursor += length + GAP_S
        spoken_end = cursor - GAP_S
        if spoken_end > end:
            warnings.append(f"{shot['id']}: narration ends {spoken_end - end:.1f}s after the shot "
                            f"(lengthen duration_s to {spoken_end - start + 0.3:.1f})")
        t = end
    total = t + storyboard["end_card"]["duration_s"]
    return shots, lines, total, warnings


def narration_pcm(lines, total_s):
    """One continuous narration track with every line placed at its start time."""
    track = bytearray(int(total_s * SAMPLE_RATE) * 2)
    for line in lines:
        offset = int(line["start"] * SAMPLE_RATE) * 2
        track[offset:offset + len(line["pcm"])] = line["pcm"]
    return bytes(track[:int(total_s * SAMPLE_RATE) * 2])


def _srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _fits(text, width):
    return len(textwrap.wrap(text, width)) <= 2


def _split_for_cards(text, width):
    """Split a subtitle into cards of at most two rows. Prefer breaking after
    punctuation near the middle, so each card reads as a natural phrase."""
    if _fits(text, width):
        return [text]
    words = text.split()
    middle = len(text) / 2
    best = None
    for i in range(1, len(words)):
        left, right = " ".join(words[:i]), " ".join(words[i:])
        if not (_fits(left, width) and _fits(right, width)):
            continue
        score = abs(len(left) - middle) - (20 if words[i - 1][-1] in ".,:;?!" else 0)
        if best is None or score < best[0]:
            best = (score, left, right)
    if best is None:  # very long line: fall back to plain two-row chunks
        rows = textwrap.wrap(text, width)
        return [" ".join(rows[i:i + 2]) for i in range(0, len(rows), 2)]
    return [best[1], best[2]]


def srt(lines, end_card, total_s, width=38, include_end_card=True):
    """Subtitles: at most two lines of ~38 characters on screen at once, as the brief
    suggests. A longer line is split into consecutive two-line cards, with its time
    shared out in proportion to the text in each card."""
    cards = []
    for line in lines:
        chunks = ["\n".join(textwrap.wrap(part, width)) for part in _split_for_cards(line["subtitle"], width)]
        total_chars = sum(len(c) for c in chunks)
        t = line["start"]
        for chunk in chunks:
            share = (line["end"] - line["start"]) * len(chunk) / total_chars
            cards.append((t, t + share, chunk))
            t += share
    if include_end_card:
        cards.append((total_s - end_card["duration_s"], total_s, end_card["text"]))
    blocks = [f"{n}\n{_srt_time(a)} --> {_srt_time(b)}\n{text}\n"
              for n, (a, b, text) in enumerate(cards, 1)]
    return "\n".join(blocks)
