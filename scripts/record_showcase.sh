#!/bin/sh
# Optional authoring helper. Run from the project checkout after installing
# asciinema and Pillow into .venv; this records locally and never uploads.
set -eu
umask 077
media_tmp=$(mktemp -d "${TMPDIR:-/tmp}/truemsg-media.XXXXXX")
trap 'rm -rf -- "$media_tmp"' EXIT HUP INT TERM
mkdir -p "$media_tmp/home" "$media_tmp/xdg" "$media_tmp/asciinema" "$media_tmp/tmp"
media_bin="${VENV_BIN:-$PWD/.venv/bin}"
env -i PATH="$media_bin:/opt/homebrew/bin:/usr/bin:/bin" \
  HOME="$media_tmp/home" TMPDIR="$media_tmp/tmp" \
  XDG_CONFIG_HOME="$media_tmp/xdg" ASCIINEMA_CONFIG_HOME="$media_tmp/asciinema" \
  PYTHONUTF8=1 PYTHONNOUSERSITE=1 LANG=en_US.UTF-8 NO_COLOR=1 \
  GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 SHELL=/bin/sh TERM=xterm-256color \
  "$media_bin/asciinema" rec --overwrite --cols 120 --rows 45 \
  -t 'truemsg: actual synthetic CLI / labelled field views' \
  -c 'python scripts/showcase.py --raw-out assets/showcase-raw.json' assets/demo.cast
