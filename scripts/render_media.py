"""Render truthful CLI excerpts from an unmodified local asciicast.

Authoring dependency: Pillow (not a truemsg runtime dependency). The terminal
contains labelled JSON projections emitted by scripts/showcase.py. Raw CLI
stdout/stderr is preserved in assets/showcase-raw.json. PNGs wrap lines; the
three-frame GIF uses reading holds instead of pretending to be real-time.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = "#101524"
PANEL = "#1a2236"
PAPER = "#f4f1e9"
MUTED = "#aab4cb"
BLUE = "#9bb8ff"
AMBER = "#f2ca7a"
RED = "#f2a5a0"


def face(size, *, mono=False, cjk=False):
    if cjk:
        options = [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]
    elif mono:
        options = [
            "/System/Library/Fonts/Menlo.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ]
    else:
        options = [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for path in options:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Install a listed system font; do not silently render unreadable glyphs")


def mixed_wrap(text, width=1144, size=21):
    mono, cjk = face(size, mono=True), face(size, cjk=True)
    result = []
    for original in text.expandtabs(4).splitlines():
        line, pixels = "", 0.0
        for char in original:
            font = cjk if ord(char) > 127 else mono
            amount = font.getlength(char)
            if pixels + amount > width:
                result.append(line)
                line, pixels = "", 0.0
            line += char
            pixels += amount
        result.append(line)
    return result


def mixed_draw(draw, xy, text, fill, size=21):
    x, y = xy
    mono, cjk = face(size, mono=True), face(size, cjk=True)
    for char in text:
        font = cjk if ord(char) > 127 else mono
        draw.text((x, y), char, font=font, fill=fill)
        x += font.getlength(char)


def terminal(title, text, height=None):
    lines = mixed_wrap(text)
    natural = 184 + len(lines) * 27
    height = height or max(440, natural)
    if natural > height:
        raise ValueError(f"Excerpt does not fit: {title}")
    image = Image.new("RGB", (1280, height), INK)
    draw = ImageDraw.Draw(image)
    draw.text((44, 25), "truemsg", font=face(30, mono=True), fill=BLUE)
    draw.text((44, 73), title, font=face(25), fill=PAPER)
    draw.text((747, 33), "ACTUAL CLI  /  SYNTHETIC FIXTURES", font=face(16, mono=True), fill=MUTED)
    draw.rounded_rectangle((26, 117, 1254, height - 38), radius=14, fill=PANEL)
    for index, line in enumerate(lines):
        fill = BLUE if line.startswith("$ ") else PAPER
        if '"FAIL"' in line or line == "[exit 1]":
            fill = RED
        elif '"WARN"' in line or "semantic_verified" in line or "requires_review" in line:
            fill = AMBER
        elif line.startswith(("[JSON", "[showcase", "[exit ")):
            fill = MUTED
        mixed_draw(draw, (48, 136 + index * 27), line, fill)
    draw.text(
        (44, height - 27),
        "Labelled JSON field view; full unmodified results: showcase-raw.json",
        font=face(15),
        fill=MUTED,
    )
    return image


def icon(draw, xy, scale=1):
    x, y = xy
    draw.rounded_rectangle((x, y, x + 96 * scale, y + 96 * scale), radius=24 * scale, fill=PANEL)
    draw.rounded_rectangle(
        (x + 17 * scale, y + 17 * scale, x + 63 * scale, y + 57 * scale),
        radius=7 * scale,
        outline=BLUE,
        width=4 * scale,
    )
    draw.line(
        (x + 28 * scale, y + 30 * scale, x + 50 * scale, y + 30 * scale), fill=BLUE, width=3 * scale
    )
    draw.line(
        (x + 28 * scale, y + 42 * scale, x + 43 * scale, y + 42 * scale), fill=BLUE, width=3 * scale
    )
    draw.rounded_rectangle(
        (x + 39 * scale, y + 41 * scale, x + 79 * scale, y + 79 * scale),
        radius=6 * scale,
        fill=PANEL,
        outline=AMBER,
        width=4 * scale,
    )
    draw.line(
        (x + 48 * scale, y + 54 * scale, x + 59 * scale, y + 54 * scale),
        fill=AMBER,
        width=3 * scale,
    )
    draw.line(
        (x + 66 * scale, y + 62 * scale, x + 66 * scale, y + 74 * scale),
        fill=AMBER,
        width=3 * scale,
    )
    draw.line(
        (x + 60 * scale, y + 68 * scale, x + 72 * scale, y + 68 * scale),
        fill=AMBER,
        width=3 * scale,
    )


def social():
    image = Image.new("RGB", (1280, 640), INK)
    draw = ImageDraw.Draw(image)
    icon(draw, (63, 58))
    draw.text((183, 67), "truemsg", font=face(78), fill=PAPER)
    draw.text((64, 239), "Offline message–diff signals", font=face(43), fill=PAPER)
    draw.text((64, 295), "for code reviewers.", font=face(43), fill=BLUE)
    draw.text((66, 400), "A second look at what a commit claims.", font=face(23), fill=MUTED)
    draw.text((66, 504), "CHECK  /  DRAFT  /  OPTIONAL HOOK", font=face(21, mono=True), fill=PAPER)
    draw.text(
        (66, 562), "PYTHON 3.11+  ·  MIT  ·  SOURCE v0.2.0", font=face(18, mono=True), fill=MUTED
    )
    for y, label in [(140, "COMMIT CLAIM"), (315, "OBSERVABLE DIFF")]:
        draw.rounded_rectangle((844, y, 1216, y + 136), radius=16, fill=PANEL)
        draw.text((865, y + 19), label, font=face(17, mono=True), fill=MUTED)
    draw.text((865, 194), "feat: add payments", font=face(23, mono=True), fill=PAPER)
    draw.text((865, 369), "tests/test_payments.py", font=face(20, mono=True), fill=AMBER)
    draw.text((865, 404), "+2 lines", font=face(22, mono=True), fill=PAPER)
    draw.line((1030, 284, 1030, 306), width=3, fill=BLUE)
    draw.text((862, 482), "Inspect this claim.", font=face(25), fill=AMBER)
    draw.text((862, 524), "Signals, not semantic proof.", font=face(19), fill=MUTED)
    draw.text((862, 572), "SCHEMATIC / NOT CLI OUTPUT", font=face(14, mono=True), fill=MUTED)
    return image


def badge(label, value):
    left, right = 20 + 7 * len(label), 20 + 7 * len(value)
    escaped_label, escaped_value = html.escape(label), html.escape(value)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{left + right}" height="24" role="img" aria-label="{escaped_label}: {escaped_value}"><rect width="{left + right}" height="24" rx="5" fill="#283249"/><path d="M{left} 0h{right - 5}q5 0 5 5v14q0 5-5 5h-{right - 5}z" fill="#41577b"/><g fill="#f4f1e9" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11" text-anchor="middle"><text x="{left / 2}" y="16">{escaped_label}</text><text x="{left + right / 2}" y="16">{escaped_value}</text></g></svg>\n'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cast", type=Path, default=Path("assets/demo.cast"))
    parser.add_argument("--out", type=Path, default=Path("assets"))
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.cast.read_text(encoding="utf-8").splitlines()]
    transcript = "".join(row[2] for row in rows[1:] if row[1] == "o").replace("\r\n", "\n")
    if "\x1b" in transcript or "\r" in transcript:
        raise ValueError(
            "Unexpected terminal controls; record NO_COLOR=1 without rewriting the cast"
        )
    if re.search(r"/(?:Users|home|private|tmp)/", transcript, re.IGNORECASE):
        raise ValueError("Do not publish recordings containing machine or private audit paths")
    sections = {}
    for chunk in re.split(r"(?m)^=== CASE: ", transcript)[1:]:
        header, body = chunk.split(" ===\n", 1)
        sections[header] = body.strip() + "\n"
    titles = {
        "matching": "A lexical match still needs review",
        "mismatch": "Feature wording, tests-only diff",
        "evidence": "No supported keywords is not a pass",
        "suggest": "A draft that explicitly requires review",
        "hooks": "Existing hooks are preserved",
        "git-boundary": "A Git option is not a commit ref",
    }
    if set(sections) != set(titles):
        raise ValueError("Expected all six actual showcase cases")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "terminal.txt").write_text(transcript, encoding="utf-8")
    for key, title in titles.items():
        terminal(title, sections[key]).save(out / f"feature-{key}.png", optimize=True)
        (out / f"feature-{key}.txt").write_text(sections[key], encoding="utf-8")
    chosen = ["matching", "mismatch", "evidence"]
    frame_height = max(900, *(184 + len(mixed_wrap(sections[key])) * 27 for key in chosen))
    frames = [terminal(titles[key], sections[key], height=frame_height) for key in chosen]
    frames[0].save(
        out / "demo.gif",
        save_all=True,
        append_images=frames[1:],
        duration=[3200, 3800, 4200],
        loop=0,
        disposal=2,
        optimize=False,
    )
    social().save(out / "social-preview.png", optimize=True)
    source_version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
    for name, pair in {
        "ci": ("CI", "prepared"),
        "license": ("license", "MIT"),
        "version": ("source", "v" + source_version),
        "python": ("Python", "3.11+"),
        "stars": ("stars", "pending"),
    }.items():
        (out / f"badge-{name}.svg").write_text(badge(*pair), encoding="utf-8")
    manifest = {
        "showcase_script_sha256": hashlib.sha256(
            Path("scripts/showcase.py").read_bytes()
        ).hexdigest(),
        "renderer_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "raw_results_sha256": hashlib.sha256(
            (args.cast.parent / "showcase-raw.json").read_bytes()
        ).hexdigest(),
        "cast_sha256": hashlib.sha256(args.cast.read_bytes()).hexdigest(),
        "cast_events": len(rows) - 1,
        "case_count": len(sections),
        "source_version": source_version,
        "rendering": "Faithful render of showcase's labelled JSON projection and actual Git output; CRLF -> LF and visual wrapping only. Full unmodified CLI stdout/stderr in showcase-raw.json.",
        "gif": {
            "cases": chosen,
            "frame_holds_ms": [3200, 3800, 4200],
            "timing": "readability holds, not recorded execution speed",
        },
        "social_preview": "Code-native schematic, not a running CLI screenshot",
        "assets": {},
    }
    for path in out.glob("*"):
        if path.name.startswith("readme-"):
            continue
        if path.suffix in {".png", ".gif"}:
            with Image.open(path) as image:
                manifest["assets"][path.name] = {
                    "width": image.width,
                    "height": image.height,
                    "frames": getattr(image, "n_frames", 1),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
    (out / "recording.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
