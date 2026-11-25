"""Stage: keyframes. One still image per shot, all in the same style and with the
same character, generated on Cloudflare Workers AI (FLUX.2 klein).

Two commands:
  make references   4 candidate reference images per character (seeds 1-4).
                    You look at them, pick one per character, and write its seed
                    into storyboard.json -> style.reference_seeds.
  make keyframes    One keyframe per shot, conditioned on the chosen references of
                    the characters in that shot, plus a contact sheet to review.

Every image is cached by a hash of everything that produced it (prompt, size, seed,
model, and the hash of each reference used). Change one shot's prompt and only that
shot is regenerated; change a reference and every shot that uses it is regenerated.
"""

import subprocess
import sys

from .common import ROOT, StageCache, input_hash, run_ffmpeg
from .providers import IMAGE_MODEL, cloudflare_image, image_extension
from .validate import load_storyboard

KEYFRAME_W, KEYFRAME_H = 720, 1280      # 9:16, divisible by 16 for the video model
REFERENCE_SIZE = 1024
CANDIDATE_SEEDS = (1, 2, 3, 4)


def reference_prompt(storyboard, name):
    description = storyboard["style"]["characters"][name]
    return (f"{storyboard['style']['style_block']}. Character reference: {description}. "
            "One single three-quarter view, alone and centred on a plain warm paper "
            "background, nothing else in the frame")


def keyframe_prompt(storyboard, shot):
    """Style block + fixed descriptions of the shot's characters + the shot itself."""
    parts = [storyboard["style"]["style_block"]]
    parts += [storyboard["style"]["characters"][c] for c in shot["characters"]]
    parts.append(shot["keyframe_prompt"])
    parts.append("Painted in the same hand-painted gouache illustration style as the rest of the film")
    return ". ".join(parts)


def find_output(cache, stem):
    """The cached file for a stem, whatever extension the model returned."""
    for name in cache.manifest:
        if name.rsplit(".", 1)[0] == stem and (cache.dir / name).exists():
            return name
    return None


def generate(cache, stem, inputs, **kwargs):
    """Generate one image unless an identical one is cached. Returns the file name."""
    digest = input_hash(inputs)
    existing = find_output(cache, stem)
    if existing and cache.manifest.get(existing) == digest:
        return existing, False
    image = cloudflare_image(**kwargs)
    name = stem + image_extension(image)
    if existing and existing != name:
        (cache.dir / existing).unlink(missing_ok=True)
        cache.manifest.pop(existing, None)
    (cache.dir / name).write_bytes(image)
    cache.record(name, digest)
    return name, True


def as_png(path, size=512):
    """Reference images are sent at 512 px, the size the model accepts as input."""
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(path),
         "-vf", f"scale={size}:{size}:force_original_aspect_ratio=decrease",
         "-f", "image2pipe", "-vcodec", "png", "-"],
        cwd=ROOT, capture_output=True, check=True).stdout


def make_references(storyboard):
    cache = StageCache("references")
    for name in storyboard["style"]["characters"]:
        prompt = reference_prompt(storyboard, name)
        for seed in CANDIDATE_SEEDS:
            inputs = {"model": IMAGE_MODEL, "prompt": prompt, "seed": seed,
                      "w": REFERENCE_SIZE, "h": REFERENCE_SIZE}
            file, made = generate(cache, f"{name}_seed{seed}", inputs, prompt=prompt,
                                  stage="references", seed=seed,
                                  width=REFERENCE_SIZE, height=REFERENCE_SIZE)
            print(f"{'made  ' if made else 'cached'}  references/{file}")
    print("\nLook at outputs/references/, pick the best candidate per character, and set\n"
          'storyboard.json -> style -> "reference_seeds": {"robel": N, "jebena": N}')


def make_keyframes(storyboard):
    chosen = storyboard["style"].get("reference_seeds", {})
    refs = StageCache("references")
    cache = StageCache("keyframes")
    # Check every reference before calling any model, so a missing one costs nothing.
    for shot in storyboard["shots"]:
        for name in shot["characters"]:
            if name not in chosen:
                raise SystemExit(f"{shot['id']} uses '{name}' but no reference is chosen: "
                                 "run make references and set style.reference_seeds")
            if find_output(refs, f"{name}_seed{chosen[name]}") is None:
                raise SystemExit(f"reference {name}_seed{chosen[name]} not found: run make references")
    made_count = 0
    for shot in storyboard["shots"]:
        references, ref_hashes = [], []
        for name in shot["characters"]:
            file = find_output(refs, f"{name}_seed{chosen[name]}")
            references.append((file, as_png(refs.dir / file)))
            ref_hashes.append(refs.manifest[file])
        prompt = keyframe_prompt(storyboard, shot)
        inputs = {"model": IMAGE_MODEL, "prompt": prompt, "seed": shot["seed"],
                  "w": KEYFRAME_W, "h": KEYFRAME_H, "references": ref_hashes}
        file, made = generate(cache, shot["id"], inputs, prompt=prompt, stage="keyframes",
                              shot=shot["id"], seed=shot["seed"], width=KEYFRAME_W,
                              height=KEYFRAME_H, references=references)
        made_count += made
        print(f"{'made  ' if made else 'cached'}  keyframes/{file}")
    contact_sheet(storyboard, cache)
    print(f"\nkeyframes: {made_count} generated, {len(storyboard['shots']) - made_count} reused. "
          "Review outputs/keyframes/contact_sheet.jpg")


def contact_sheet(storyboard, cache, per_row=5, w=288, h=512):
    """All keyframes in one image, to check style and character consistency at a glance."""
    files = [find_output(cache, s["id"]) for s in storyboard["shots"]]
    args, chains, layout = [], [], []
    for i, file in enumerate(files):
        args += ["-i", f"outputs/keyframes/{file}"]
        chains.append(f"[{i}:v]scale={w}:{h}[k{i}]")
        layout.append(f"{(i % per_row) * w}_{(i // per_row) * h}")
    stack = "".join(f"[k{i}]" for i in range(len(files)))
    graph = ";".join(chains) + f";{stack}xstack=inputs={len(files)}:layout={'|'.join(layout)}:fill=black"
    run_ffmpeg([*args, "-filter_complex", graph, "-frames:v", "1", "-q:v", "3",
                "outputs/keyframes/contact_sheet.jpg"], stage="keyframes", label="contact sheet")


def main():
    storyboard = load_storyboard()
    if sys.argv[1:] == ["references"]:
        make_references(storyboard)
    else:
        make_keyframes(storyboard)


if __name__ == "__main__":
    main()
