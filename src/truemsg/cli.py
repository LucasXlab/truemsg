"""Offline CLI for limited message/diff consistency signals."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from rich.console import Console

from . import analyze, git, hooks, report
from . import config as configmod
from . import diff as diffmod
from . import message as msgmod

HOOK_SCRIPT = hooks.HOOK_SCRIPT  # Public compatibility alias.
ERRORS = (git.GitError, configmod.ConfigError, diffmod.DiffError, hooks.HookError, OSError)


def _env(name: str) -> Optional[str]:
    return os.environ.get(name) or None


def _resolve_check(args) -> tuple:
    if args.ref and (args.range or args.pr):
        raise git.GitError("--ref cannot be combined with --range or --pr")
    if not args.pr and (args.base or args.head):
        raise git.GitError("--base/--head require --pr")
    if args.pr:
        title = args.title or _env("GITHUB_PR_TITLE") or _env("PR_TITLE")
        body = args.body or _env("GITHUB_PR_BODY") or _env("PR_BODY") or ""
        if not title:
            raise git.GitError("PR mode requires --title or GITHUB_PR_TITLE")
        if args.range and (args.base or args.head):
            raise git.GitError("Use either --range or --base/--head in PR mode")
        if args.range:
            selection = args.range
        else:
            base = args.base or _env("GITHUB_BASE_REF") or "origin/main"
            head = args.head or _env("GITHUB_HEAD_REF") or "HEAD"
            selection = f"{base}...{head}"
        return title + ("\n\n" + body if body else ""), selection, True
    if args.range:
        _, right, _ = git.resolve_range(args.range)
        message = args.title or git.get_commit_message(right)
        if args.body:
            message += "\n\n" + args.body
        return message, args.range, True
    ref = args.ref or "HEAD"
    message = args.title or git.get_commit_message(ref)
    if args.body:
        message += "\n\n" + args.body
    return message, ref, False


def _load_cfg(args):
    return configmod.load_config(getattr(args, "config", None), start_dir=git.repo_root())


def _get_files(selection: str, is_range: bool = True) -> List[dict]:
    return diffmod.parse_diff(
        git.get_diff(selection) if is_range else git.get_commit_diff(selection)
    )


def cmd_check(args) -> int:
    try:
        msg_text, selection, is_range = _resolve_check(args)
        cfg = _load_cfg(args)
        msg = msgmod.parse_message(msg_text)
        files = _get_files(selection, is_range)
        result = analyze.analyze(msg, files, config=cfg)
    except ERRORS as exc:
        print(f"[truemsg] {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(report.render_json(result, msg, files))
    else:
        report.render_console(
            Console(no_color=args.no_color or bool(_env("NO_COLOR"))), result, msg, files
        )
    fail_on = args.fail_on if args.fail_on is not None else cfg["fail_on"]
    return int(result["verdict"] == "FAIL" or (fail_on == "warn" and result["verdict"] == "WARN"))


def cmd_suggest(args) -> int:
    try:
        if args.range and args.ref:
            raise git.GitError("--ref cannot be combined with --range")
        cfg = _load_cfg(args)
        files = _get_files(args.range or args.ref or "HEAD", args.range is not None)
        files = [f for f in files if not configmod.is_ignored(f["path"], cfg["ignore"])]
        suggestion = analyze.suggest_message(files)
    except ERRORS as exc:
        print(f"[truemsg] {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(suggestion, ensure_ascii=True, indent=2)
        if args.json
        else suggestion["conventional"]
    )
    return 0


def cmd_hook(args) -> int:
    try:
        if not git.is_repo():
            raise git.GitError("Current directory is not a Git working tree")
        print("[truemsg] " + hooks.update_hook(uninstall=args.uninstall))
        return 0
    except ERRORS as exc:
        print(f"[truemsg] {exc}", file=sys.stderr)
        return 2


def cmd_pre_push(args) -> int:
    try:
        payload = sys.stdin.read(1024 * 1024 + 1)
        commits = hooks.pushed_commits(payload)
    except ERRORS as exc:
        print(f"[truemsg] {exc}", file=sys.stderr)
        return 2
    for oid in commits:
        check = argparse.Namespace(
            pr=False,
            title=None,
            body=None,
            ref=oid,
            range=None,
            base=None,
            head=None,
            config=None,
            json=False,
            no_color=True,
            fail_on="warn",
        )
        status = cmd_check(check)
        if status:
            return status
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truemsg",
        description="Offline lexical signals for commit/PR review; not a semantic truth check.",
    )
    parser.add_argument(
        "--version", action="version", version=f"truemsg {__import__('truemsg').__version__}"
    )
    sub = parser.add_subparsers(dest="cmd")
    check = sub.add_parser("check", help="Check a commit, endpoint range or PR title")
    check.add_argument(
        "--range", help="A..B endpoint diff or A...B merge-base diff; message defaults to B"
    )
    check.add_argument(
        "--ref", help="Single commit, including initial commits; merge uses first parent"
    )
    check.add_argument(
        "--pr", action="store_true", help="PR title/body against merge-base diff by default"
    )
    check.add_argument("--base", help="PR base, defaults to GITHUB_BASE_REF or origin/main")
    check.add_argument("--head", help="PR head, defaults to GITHUB_HEAD_REF or HEAD")
    check.add_argument("--title", help="Explicit message/PR title")
    check.add_argument("--body", help="Explicit message/PR body")
    check.add_argument("--config", help="Explicit policy path; errors do not fall back")
    check.add_argument("--json", action="store_true")
    check.add_argument(
        "--fail-on", choices=["fail", "warn"], default=None, help="Override policy exit threshold"
    )
    check.add_argument("--no-color", action="store_true")
    check.set_defaults(func=cmd_check)
    suggest = sub.add_parser("suggest", help="Draft a deterministic message for manual review")
    suggest.add_argument("--range")
    suggest.add_argument("--ref")
    suggest.add_argument("--config")
    suggest.add_argument("--json", action="store_true")
    suggest.set_defaults(func=cmd_suggest)
    hook = sub.add_parser("hook", help="Explicit ownership-safe pre-push hook setup")
    choices = hook.add_mutually_exclusive_group(required=True)
    choices.add_argument("--install", action="store_true")
    choices.add_argument("--uninstall", action="store_true")
    hook.set_defaults(func=cmd_hook)
    pre_push = sub.add_parser("_pre-push", help=argparse.SUPPRESS)
    pre_push.add_argument("remote", nargs="?")
    pre_push.add_argument("location", nargs="?")
    pre_push.set_defaults(func=cmd_pre_push)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
