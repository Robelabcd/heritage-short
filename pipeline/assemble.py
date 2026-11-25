"""Stage: assembly. Builds the finished film from the storyboard, in code.

For every shot it uses the moving clip from the video stage if one exists
(outputs/clips/<shot>.mp4), and otherwise animates the keyframe with a slow
pan-and-zoom (Ken Burns). Then it adds the end card, the narration placed by the
timeline, the score ducked under the voice, burned-in subtitles and loudness
normalisation, and exports both aspect ratios:

  outputs/film/film_9x16.mp4    1080x1920, the main version (phones)
  outputs/film/film_16x9.mp4    1920x1080, the 9:16 picture over a blurred copy of itself

Each shot's segment is cached by a hash of its inputs, so changing one shot
re-renders only that segment.

Run with: make assemble
"""

import subprocess
import wave

from .common import OUTPUTS, ROOT, StageCache, input_hash, run_ffmpeg, video_encoder_args
from .keyframes import find_output
from .timeline import SAMPLE_RATE, build, narration_pcm, srt
from .validate import load_storyboard

STAGE = "assemble"
W, H, FPS = 1080, 1920, 24
OUT = OUTPUTS / "film"
PLACEHOLDER = ("0.05*(sin(2*PI*220*t)+0.7*sin(2*PI*261.63*t)+0.6*sin(2*PI*329.63*t))"
               "*(0.75+0.25*sin(2*PI*0.1*t))")
SUB_STYLE_9x16 = ("FontName=Helvetica,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                  "BorderStyle=1,Outline=1.2,Shadow=0,Alignment=2,MarginV=48")
SUB_STYLE_16x9 = ("FontName=Helvetica,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                  "BorderStyle=1,Outline=1.2,Shadow=0,Alignment=2,MarginV=22")


def ken_burns(motion, index, frames):
    """A slow camera move chosen from the shot's motion prompt.
    zoompan needs zoom (z) and the top-left corner (x, y) of the visible window."""
    n = max(frames - 1, 1)
    centre_x, centre_y = "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    if "static" in motion:                                   # nearly still
        return f"1+0.04*on/{n}", centre_x, centre_y
    if "pan" in motion or "orbit" in motion:                 # drift sideways
        return "1.10", f"(iw-iw/zoom)*on/{n}", centre_y
    if "push-in" in motion or index % 2 == 0:                # move closer
        return f"1+0.12*on/{n}", centre_x, centre_y
    return f"1.12-0.12*on/{n}", centre_x, centre_y           # pull back


def render_segment(shot, index, keyframe, clip, path):
    frames = round(shot["duration_s"] * FPS)
    if clip:   # a moving clip: slow it down a little if short, then hold the last frame
        length = clip_length(clip)
        stretch = min(shot["duration_s"] / length, 1.6) if length else 1
        vf = (f"setpts={stretch:.4f}*PTS,scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},fps={FPS},tpad=stop_mode=clone:stop_duration={shot['duration_s']},"
              f"trim=duration={shot['duration_s']},setsar=1")
        inputs = ["-i", clip]
    else:      # a still keyframe: upscale first so the slow zoom stays smooth
        z, x, y = ken_burns(shot["motion_prompt"], index, frames)
        vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={W}x{H}:fps={FPS},setsar=1")
        inputs = ["-loop", "1", "-i", keyframe]
    run_ffmpeg([*inputs, "-vf", vf, "-frames:v", str(frames), "-an",
                *video_encoder_args(), "-r", str(FPS), str(path)],
               stage=STAGE, label=f"segment {shot['id']}")


def clip_length(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], cwd=ROOT, capture_output=True, text=True).stdout
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


def render_end_card(end_card, path):
    """The end card: centred text on a warm dark background, drawn with the subtitles renderer."""
    card_srt = OUT / "end_card.srt"
    card_srt.write_text(f"1\n00:00:00,000 --> 00:00:{end_card['duration_s']:02.0f},000\n"
                        f"{end_card['text']}\n", encoding="utf-8")
    style = ("FontName=Helvetica,FontSize=15,PrimaryColour=&H00E8F0F5,BorderStyle=1,Outline=0,"
             "Shadow=0,Alignment=10,MarginL=30,MarginR=30")
    run_ffmpeg(["-f", "lavfi", "-i", f"color=c=0x1c1612:s={W}x{H}:r={FPS}:d={end_card['duration_s']}",
                "-vf", f"subtitles=outputs/film/end_card.srt:force_style='{style}',setsar=1",
                "-an", *video_encoder_args(), str(path)], stage=STAGE, label="end card")


# Every filter this stage uses. All are LGPL, so they exist in every common FFmpeg
# build, including conda-forge's (which leaves out GPL filters such as boxblur and eq).
REQUIRED_FILTERS = ["zoompan", "tpad", "subtitles", "sidechaincompress", "amix", "loudnorm",
                    "afade", "apad", "gblur", "lutyuv", "overlay", "concat"]


def check_ffmpeg_filters():
    """Fail early, with a clear list, if this FFmpeg build lacks a filter we need."""
    listing = subprocess.run(["ffmpeg", "-hide_banner", "-filters"],
                             capture_output=True, text=True).stdout
    missing = [f for f in REQUIRED_FILTERS if f" {f} " not in listing]
    if missing:
        raise SystemExit(f"this ffmpeg build lacks filters: {', '.join(missing)}")


def main():
    storyboard = load_storyboard()
    check_ffmpeg_filters()
    OUT.mkdir(parents=True, exist_ok=True)
    keyframes, clips = StageCache("keyframes"), StageCache("clips")
    segments = StageCache("segments")

    # 1. One video segment per shot (cached), then the end card.
    parts = []
    for i, shot in enumerate(storyboard["shots"]):
        kf = find_output(keyframes, shot["id"])
        if kf is None:
            raise SystemExit(f"{shot['id']}: no keyframe, run make keyframes")
        clip = find_output(clips, shot["id"])
        source = (f"outputs/clips/{clip}" if clip else f"outputs/keyframes/{kf}")
        digest = input_hash({"source": source,
                             "source_hash": (clips.manifest if clip else keyframes.manifest)[clip or kf],
                             "duration": shot["duration_s"], "motion": shot["motion_prompt"],
                             "index": i, "size": [W, H, FPS]})
        name = f"{shot['id']}.mp4"
        if not segments.is_fresh(name, digest):
            render_segment(shot, i, f"outputs/keyframes/{kf}", source if clip else None,
                           segments.dir / name)
            segments.record(name, digest)
            print(f"made    segment {shot['id']} ({'clip' if clip else 'pan-and-zoom'})")
        parts.append(segments.dir / name)
    render_end_card(storyboard["end_card"], OUT / "end_card.mp4")
    parts.append(OUT / "end_card.mp4")

    concat_list = OUT / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy",
                "outputs/film/picture.mp4"], stage=STAGE, label="concat picture")

    # 2. Sound: narration placed by the timeline, score ducked under it.
    _, lines, total, warnings = build(storyboard)
    for w in warnings:
        print(f"WARNING  {w}")
    with wave.open(str(OUT / "narration.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(narration_pcm(lines, total))
    (OUT / "subtitles.srt").write_text(
        srt(lines, storyboard["end_card"], total, include_end_card=False), encoding="utf-8")

    score = OUTPUTS / "music" / "score.wav"
    music_in = (["-i", "outputs/music/score.wav"] if score.exists()
                else ["-f", "lavfi", "-i", f"aevalsrc={PLACEHOLDER}:s=48000:d={total:.2f}"])
    audio = (f"[1:a]aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[voice][key];"
             f"[2:a]aresample=48000,aformat=channel_layouts=stereo,"
             f"volume={storyboard['music'].get('gain_db', -12)}dB,apad,atrim=0:{total:.2f},"
             f"afade=t=in:d=1.5,afade=t=out:st={total - 4:.2f}:d=4[music];"
             "[music][key]sidechaincompress=threshold=0.02:ratio=6:attack=300:release=1500[ducked];"
             "[voice][ducked]amix=inputs=2:duration=first:normalize=0,"
             "loudnorm=I=-14:TP=-1.5:LRA=11[mix]")

    # 3. Both aspect ratios, each with subtitles laid out for its own frame.
    versions = {
        "film_9x16.mp4": (f"[0:v]subtitles=outputs/film/subtitles.srt:force_style='{SUB_STYLE_9x16}'[v]"),
        "film_16x9.mp4": ("[0:v]split=2[bg][fg];"
                          "[bg]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
                          "gblur=sigma=30,lutyuv=y=val*0.85[bgb];"
                          "[fg]scale=-2:1080[fgs];[bgb][fgs]overlay=(W-w)/2:0,"
                          f"subtitles=outputs/film/subtitles.srt:force_style='{SUB_STYLE_16x9}'[v]"),
    }
    for name, video in versions.items():
        run_ffmpeg(["-i", "outputs/film/picture.mp4", "-i", "outputs/film/narration.wav", *music_in,
                    "-filter_complex", f"{audio};{video}", "-map", "[v]", "-map", "[mix]",
                    *video_encoder_args(), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-t", f"{total:.2f}", "-movflags", "+faststart", f"outputs/film/{name}"],
                   stage=STAGE, label=name)
        print(f"film: outputs/film/{name}  ({total:.1f}s)")
    print(f"music: {'outputs/music/score.wav' if score.exists() else 'placeholder chord (no score yet)'}")


if __name__ == "__main__":
    main()
