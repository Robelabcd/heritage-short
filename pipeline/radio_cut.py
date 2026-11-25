"""Radio cut: narration over placeholder music on a black screen, with subtitles.

The cheapest prototype of the film: it tests the story and its timing before
any picture exists. Output: outputs/radio/radio_cut.mp4 (9:16, ready for WhatsApp).

Run with: make radio-cut   (runs the narration stage first)
"""

import wave

from .common import OUTPUTS, run_ffmpeg, video_encoder_args
from .timeline import SAMPLE_RATE, build, narration_pcm, srt
from .validate import load_storyboard

STAGE = "radio_cut"
OUT = OUTPUTS / "radio"

# Placeholder music: a soft A-minor chord with a slow swell. Replaced by the real
# score in the music stage; here it only shows where music will sit.
PLACEHOLDER = ("0.05*(sin(2*PI*220*t)+0.7*sin(2*PI*261.63*t)+0.6*sin(2*PI*329.63*t))"
               "*(0.75+0.25*sin(2*PI*0.1*t))")


def main():
    storyboard = load_storyboard()
    _, lines, total, warnings = build(storyboard)
    for w in warnings:
        print(f"WARNING  {w}")
    OUT.mkdir(parents=True, exist_ok=True)

    with wave.open(str(OUT / "narration_track.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(narration_pcm(lines, total))
    (OUT / "subtitles.srt").write_text(srt(lines, storyboard["end_card"], total), encoding="utf-8")

    style = ("FontName=Helvetica,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=40")
    run_ffmpeg([
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=24:d={total:.2f}",
        "-i", "outputs/radio/narration_track.wav",
        "-f", "lavfi", "-i", f"aevalsrc={PLACEHOLDER}:s=48000:d={total:.2f}",
        "-filter_complex",
        f"[2:a]afade=t=in:d=2,afade=t=out:st={total - 3:.2f}:d=3[m];"
        "[1:a]aresample=48000[v];"
        "[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a];"
        f"[0:v]subtitles=outputs/radio/subtitles.srt:force_style='{style}'[vid]",
        "-map", "[vid]", "-map", "[a]",
        *video_encoder_args(), "-c:a", "aac", "-b:a", "160k",
        "-t", f"{total:.2f}", "outputs/radio/radio_cut.mp4",
    ], stage=STAGE, label="radio cut render")
    print(f"radio cut: {total:.1f}s -> outputs/radio/radio_cut.mp4")


if __name__ == "__main__":
    main()
