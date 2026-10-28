# Media provenance and regeneration

All terminal PNGs and `demo.gif` come from a real installed `truemsg.cli` running on temporary **synthetic** Git histories. No real project or personal data is used. `logo.svg`, badges and `social-preview.png` are code-native illustrations; the social image is explicitly a schematic, not a CLI screenshot.

- `demo.cast`: unmodified local asciicast v2 from `scripts/showcase.py`.
- `showcase-raw.json`: complete, unmodified stdout/stderr for each actual CLI call, expected/actual exit code, and synthetic Git patch where shown.
- `terminal.txt`: all recorded output, with CRLF normalized to LF.
- `feature-*.png` / `feature-*.txt`: one actual showcase section each. The terminal view selects JSON fields for readability. `rule_ids` maps to `findings[].rule`; message, counts and evidence values come directly from the real JSON. It does not present the field view as unmodified native CLI output.
- `demo.gif`: matching, mismatch and insufficient-keyword excerpts held for 3.2, 3.8 and 4.2 seconds. These are reading holds, not execution timing. The cast retains real timestamps. Line wrapping is visual only.
- `recording.json`: cast SHA-256, image sizes, GIF frames, excerpt names and rendering notes.

PASS means no lexical rule conflict; it is not semantic proof. Chinese/no-keyword input gives insufficient evidence. The draft suggestion requires human review; hook and invalid-ref examples show actual controlled refusal. All exit codes are checked by the showcase script.

For optional authoring, install the checked-out project first (`make dev`), then install `asciinema` and `Pillow` in that environment. They are not runtime dependencies:

```sh
.venv/bin/python -m pip install asciinema Pillow
sh scripts/record_showcase.sh
.venv/bin/python scripts/render_media.py
```

The recorder helper uses a temporary, minimal HOME/XDG/configuration, an explicit local cast filename and no upload command. Run it from the checkout. The renderer needs Menlo/Arial/Arial Unicode on macOS, or DejaVu Sans/Mono plus Noto Sans CJK at the listed Linux locations; it fails instead of silently drawing missing glyphs. Regeneration replaces only these named media files, leaving `readme-*` assets alone.

The source is `v0.2.0`; CI is prepared and Stars are pending. The badges do not report a package-registry release or remote CI success.
