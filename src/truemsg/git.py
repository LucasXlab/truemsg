"""Bounded, read-only Git calls with validated revision arguments."""

from __future__ import annotations

import os
import re
import subprocess
import threading
from typing import List, Optional

TIMEOUT = 15
MAX_OUTPUT = 8 * 1024 * 1024
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_OID = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


class GitError(RuntimeError):
    """A controlled Git failure, without untrusted stderr or arguments."""


def git_env() -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    if "GIT_CEILING_DIRECTORIES" in os.environ:
        env["GIT_CEILING_DIRECTORIES"] = os.environ["GIT_CEILING_DIRECTORIES"]
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_NO_LAZY_FETCH": "1",
            "LC_ALL": "C",
            "GIT_PAGER": "cat",
        }
    )
    return env


def run_git(args: List[str], cwd: Optional[str] = None) -> str:
    argv = [
        "git",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.untrackedCache=false",
        "-c",
        "color.ui=false",
        "-c",
        "core.quotePath=true",
        "-c",
        "log.showSignature=false",
        *args,
    ]
    try:
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            env=git_env(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, ValueError) as exc:
        raise GitError("Unable to start Git; check Git installation and repository path") from exc
    buffers = [bytearray(), bytearray()]
    exceeded = threading.Event()

    def collect(stream, target):
        while data := stream.read(65536):
            if len(target) + len(data) > MAX_OUTPUT:
                exceeded.set()
                proc.kill()
                break
            target.extend(data)
        stream.close()

    threads = [
        threading.Thread(target=collect, args=(stream, target), daemon=True)
        for stream, target in zip((proc.stdout, proc.stderr), buffers, strict=True)
    ]
    for thread in threads:
        thread.start()
    try:
        proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        proc.kill()
        proc.wait()
        raise GitError("Git exceeded its time limit") from exc
    finally:
        for thread in threads:
            thread.join()
    if exceeded.is_set():
        raise GitError("Git output exceeded the 8 MiB limit; choose a smaller range")
    if proc.returncode:
        raise GitError("Git command failed; verify refs, repository state and available history")
    return buffers[0].decode("utf-8", errors="surrogateescape")


def is_repo(path: Optional[str] = None) -> bool:
    try:
        return run_git(["rev-parse", "--is-inside-work-tree"], cwd=path).strip() == "true"
    except GitError:
        return False


def repo_root(path: Optional[str] = None) -> str:
    return run_git(["rev-parse", "--show-toplevel"], cwd=path).removesuffix("\n")


def _require_full_objects() -> None:
    names = run_git(["config", "--local", "--name-only", "--list"]).lower().splitlines()
    if any(name == "extensions.partialclone" or name.endswith(".promisor") for name in names):
        raise GitError("Partial/promisor clones are unsupported; use a full local checkout")


def resolve_ref(ref: str) -> str:
    if not ref or ref.startswith("-") or any(ord(c) < 32 for c in ref):
        raise GitError("Invalid revision: expected a commit ref, not an option")
    _require_full_objects()
    oid = run_git(["rev-parse", "--verify", "--end-of-options", ref + "^{commit}"]).strip()
    if not _OID.fullmatch(oid):
        raise GitError("Git did not return a valid commit object")
    return oid


def resolve_range(spec: str) -> tuple[str, str, str]:
    separator = "..." if "..." in spec else ".."
    if spec.count(separator) != 1:
        raise GitError("Expected A..B (endpoint diff) or A...B (merge-base diff)")
    left, right = spec.split(separator)
    return resolve_ref(left), resolve_ref(right), separator


def get_commit_message(ref: str = "HEAD") -> str:
    return run_git(["log", "-1", "--format=%B", resolve_ref(ref), "--"]).strip()


def _diff_args() -> list[str]:
    return [
        "diff",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--no-relative",
        "--ignore-submodules=none",
        "--submodule=short",
        "--find-renames=50%",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        "--diff-algorithm=myers",
        "-U0",
    ]


def get_diff(range_spec: str) -> str:
    left, right, separator = resolve_range(range_spec)
    return run_git([*_diff_args(), left + separator + right, "--"])


def get_commit_diff(ref: str = "HEAD") -> str:
    oid = resolve_ref(ref)
    parents = run_git(["rev-list", "--parents", "-n", "1", oid, "--"]).split()
    parent = parents[1] if len(parents) > 1 else EMPTY_TREE
    if parent == EMPTY_TREE and len(oid) == 64:
        parent = run_git(["hash-object", "-t", "tree", "--stdin"]).strip()
    return run_git([*_diff_args(), parent, oid, "--"])


def hooks_path() -> str:
    return run_git(
        ["rev-parse", "--path-format=absolute", "--git-path", "hooks/pre-push"]
    ).removesuffix("\n")


def upstream_of(ref: str = "HEAD") -> Optional[str]:
    try:
        resolve_ref(ref)
        return run_git(
            [
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                "--end-of-options",
                f"{ref}@{{u}}",
            ]
        ).strip()
    except GitError:
        return None
