"""Explicit, ownership-safe pre-push hook installation and ref selection."""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

from . import git

HOOK_SCRIPT = """#!/bin/sh
# truemsg-owned-pre-push-v1
exec truemsg _pre-push "$@"
"""
_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


class HookError(ValueError):
    """A hook could not safely be installed, removed or interpreted."""


def _existing(path: Path) -> str | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode) or info.st_size > 16384:
        raise HookError("Refusing a hook that is not a small regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as source:
        opened = os.fstat(source.fileno())
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise HookError("Hook changed during inspection")
        try:
            return source.read(16385).decode("utf-8")
        except UnicodeError as exc:
            raise HookError("Refusing a non-UTF-8 hook") from exc


def update_hook(uninstall: bool = False) -> str:
    path = Path(git.hooks_path())
    # An explicit core.hooksPath is honored, but links are never followed for writes.
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise HookError("Refusing a symlink in the hook path")
    existing = _existing(path)
    if existing is not None and existing != HOOK_SCRIPT:
        raise HookError("Existing hook is not owned by truemsg; preserve it and integrate manually")
    if uninstall:
        if existing is None:
            return "No truemsg hook was installed"
        path.unlink()
        return "Removed the owned truemsg hook"
    if existing is not None:
        return "Owned truemsg hook is already installed"
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, flags, 0o755), "w", encoding="utf-8") as target:
        target.write(HOOK_SCRIPT)
    return "Installed the owned truemsg pre-push hook"


def pushed_commits(payload: str) -> list[str]:
    if len(payload) > 1024 * 1024:
        raise HookError("Pre-push input exceeded 1 MiB")
    selected = []
    for line in payload.splitlines():
        parts = line.split()
        if len(parts) != 4 or not _SHA.fullmatch(parts[1]) or not _SHA.fullmatch(parts[3]):
            raise HookError("Invalid pre-push ref update")
        local, remote = parts[1], parts[3]
        if set(local) == {"0"}:  # Deleting a remote ref introduces no commits.
            continue
        local = git.resolve_ref(local)
        if set(remote) == {"0"}:
            args = [local, "--not", "--remotes"]
        else:
            remote = git.resolve_ref(remote)
            args = [remote + ".." + local]
        for oid in git.run_git(["rev-list", "--reverse", *args, "--"]).splitlines():
            if not _SHA.fullmatch(oid):
                raise HookError("Invalid commit list returned by Git")
            if oid not in selected:
                selected.append(oid)
            if len(selected) > 1000:
                raise HookError("More than 1000 commits; review smaller ref updates")
    return selected
