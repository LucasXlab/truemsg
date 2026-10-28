"""Real installed-CLI showcase on disposable synthetic Git history.

The terminal uses explicitly labelled JSON field views. Complete, unmodified
CLI stdout/stderr and the actual synthetic diff are saved to --raw-out.
No personal repository, model, API or network is accessed.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-out", type=Path, default=Path("assets/showcase-raw.json"))
    args = parser.parse_args()
    raw_out = args.raw_out.absolute()
    records = []
    with tempfile.TemporaryDirectory(prefix="truemsg-showcase-") as temporary:
        repo = Path(temporary)
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(
            {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "Synthetic Contributor",
                "GIT_AUTHOR_EMAIL": "contributor@example.invalid",
                "GIT_COMMITTER_NAME": "Synthetic Contributor",
                "GIT_COMMITTER_EMAIL": "contributor@example.invalid",
                "NO_COLOR": "1",
            }
        )

        def git(*argv):
            result = subprocess.run(
                ["git", *argv], cwd=repo, env=env, capture_output=True, text=True, timeout=15
            )
            if result.returncode:
                raise RuntimeError("Synthetic Git setup failed")
            return result.stdout

        def record(name, title, argv, expected, *, patch=None):
            result = subprocess.run(
                [sys.executable, "-m", "truemsg.cli", *argv],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != expected:
                raise RuntimeError(f"{name}: expected exit {expected}, got {result.returncode}")
            item = {
                "name": name,
                "title": title,
                "command": ["truemsg", *argv],
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "synthetic_diff": patch,
            }
            records.append(item)
            print(f"=== CASE: {name} ===", flush=True)
            if patch:
                print("$ git show --format= --no-ext-diff --no-textconv -U0 HEAD", flush=True)
                print(patch.rstrip(), flush=True)
            print("$ " + shlex.join(item["command"]), flush=True)
            if "--json" in argv and result.stdout:
                value = json.loads(result.stdout)
                print("[JSON field view; full stdout in showcase-raw.json]", flush=True)
                if "verdict" in value:
                    selected = {
                        "verdict": value["verdict"],
                        "message": value["message"],
                        "rule_ids": [f["rule"] for f in value["findings"]],
                        "summary": {
                            key: value["summary"][key] for key in ("files", "added", "removed")
                        },
                        "evidence": {
                            key: value["evidence"][key]
                            for key in ("semantic_verified", "keywords_available")
                        },
                    }
                else:
                    selected = value
                item["field_view"] = selected
                for key, field in selected.items():
                    print(f"{key}: " + json.dumps(field, ensure_ascii=False), flush=True)
            else:
                print((result.stdout + result.stderr).rstrip(), flush=True)
            print(f"[exit {result.returncode}]", flush=True)
            return item

        git("init", "-b", "main")
        (repo / "README.md").write_text("# Synthetic showcase\n", encoding="utf-8")
        git("add", "README.md")
        git("commit", "-m", "docs: initial synthetic fixture")
        (repo / "src").mkdir()
        (repo / "src/auth.py").write_text(
            "def authenticate(token):\n    return bool(token)\n", encoding="utf-8"
        )
        git("add", "src/auth.py")
        git("commit", "-m", "feat(auth): add authenticate token handler")
        patch = git("show", "--format=", "--no-ext-diff", "--no-textconv", "-U0", "HEAD")
        match = record(
            "matching", "A lexical match still needs review", ["check", "--json"], 0, patch=patch
        )
        assert match["field_view"]["verdict"] == "PASS"
        assert match["field_view"]["evidence"]["semantic_verified"] is False
        (repo / "tests").mkdir()
        (repo / "tests/test_payments.py").write_text(
            "def test_payments():\n    assert True\n", encoding="utf-8"
        )
        git("add", "tests/test_payments.py")
        git("commit", "-m", "feat: add payment gateway")
        patch = git("show", "--format=", "--no-ext-diff", "--no-textconv", "-U0", "HEAD")
        mismatch = record(
            "mismatch", "Feature wording, tests-only diff", ["check", "--json"], 1, patch=patch
        )
        assert mismatch["field_view"]["verdict"] == "FAIL"
        assert "trivial-change" in mismatch["field_view"]["rule_ids"]
        limited = record(
            "evidence",
            "Chinese message: insufficient lexical evidence",
            [
                "check",
                "--ref",
                "HEAD~1",
                "--title",
                "fix: 修复支付漏洞",
                "--json",
                "--fail-on",
                "warn",
            ],
            1,
        )
        assert limited["field_view"]["verdict"] == "WARN"
        assert limited["field_view"]["evidence"]["keywords_available"] is False
        draft = record(
            "suggest",
            "A deterministic draft, not a verified explanation",
            ["suggest", "--ref", "HEAD~1", "--json"],
            0,
        )
        assert draft["field_view"]["requires_review"] is True
        hook = repo / ".git/hooks/pre-push"
        hook.write_text("#!/bin/sh\n# Existing synthetic guard\nexit 0\n", encoding="utf-8")
        before = hook.read_bytes()
        record("hooks", "Existing hooks are preserved", ["hook", "--install"], 2)
        assert hook.read_bytes() == before
        print("[showcase assertion] existing hook bytes unchanged: true", flush=True)
        record(
            "git-boundary",
            "An option is not a commit ref",
            ["check", "--ref=--output=unexpected.patch", "--json"],
            2,
        )
        assert not (repo / "unexpected.patch").exists()
        print("[showcase assertion] unexpected.patch absent: true", flush=True)
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw_out.write_text(
        json.dumps(
            {
                "schema": "truemsg-showcase-v1",
                "synthetic_only": True,
                "display": "Selected JSON fields are a labelled projection; stdout/stderr and diffs below are complete and unmodified.",
                "cases": records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
