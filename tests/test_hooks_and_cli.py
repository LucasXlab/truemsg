import io
import json
from pathlib import Path

import pytest
from conftest import commit_file, git_command

from truemsg import cli, git, hooks


def test_hook_preserves_unowned_and_modified_files(repo):
    commit_file(repo)
    path = Path(git.hooks_path())
    path.write_text("#!/bin/sh\necho foreign\n")
    original = path.read_bytes()
    for uninstall in [False, True]:
        with pytest.raises(hooks.HookError, match="not owned"):
            hooks.update_hook(uninstall)
        assert path.read_bytes() == original
    path.unlink()
    hooks.update_hook()
    assert path.read_text() == hooks.HOOK_SCRIPT
    assert "already" in hooks.update_hook()
    assert "Removed" in hooks.update_hook(True)
    assert "No" in hooks.update_hook(True)


def test_linked_worktree_and_configured_hooks_path(repo, tmp_path, monkeypatch):
    commit_file(repo)
    worktree = tmp_path / "linked"
    git_command("worktree", "add", "-b", "linked", str(worktree))
    monkeypatch.chdir(worktree)
    assert (worktree / ".git").is_file()
    hooks.update_hook()
    assert Path(git.hooks_path()).read_text() == hooks.HOOK_SCRIPT
    hooks.update_hook(True)
    custom = repo / ".custom-hooks"
    git_command("config", "core.hooksPath", str(custom))
    hooks.update_hook()
    assert (custom / "pre-push").exists()


def test_hook_symlink_is_never_overwritten(repo, tmp_path):
    commit_file(repo)
    sentinel = tmp_path / "sentinel"
    sentinel.write_text("preserve")
    path = Path(git.hooks_path())
    path.symlink_to(sentinel)
    with pytest.raises(hooks.HookError):
        hooks.update_hook()
    assert sentinel.read_text() == "preserve"


def test_pre_push_selects_actual_updated_refs(repo):
    first = commit_file(repo)
    second = commit_file(repo, text="value = 2\n")
    payload = f"refs/heads/main {second} refs/heads/main {first}\n"
    assert hooks.pushed_commits(payload) == [second]
    assert hooks.pushed_commits(f"(delete) {'0' * 40} refs/heads/main {second}\n") == []
    assert hooks.pushed_commits(f"refs/heads/main {second} refs/heads/new {'0' * 40}\n") == [
        first,
        second,
    ]
    with pytest.raises(hooks.HookError):
        hooks.pushed_commits("malformed input")
    with pytest.raises(hooks.HookError):
        hooks.pushed_commits("x" * (1024 * 1024 + 1))
    with pytest.raises(git.GitError):
        hooks.pushed_commits(f"refs/heads/main {second} refs/heads/main {'f' * 40}\n")


def test_cli_initial_commit_range_message_and_config_precedence(repo, capsys):
    first = commit_file(repo, message="docs: initial fixture")
    assert cli.main(["check", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["files"] == 1
    second = commit_file(
        repo,
        text="def authenticate():\n    return True\n",
        message="feat(auth): add authenticate function",
    )
    commit_file(repo, "README.md", "later\n", "docs: later unrelated title")
    assert cli.main(["check", "--range", f"{first}..{second}", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["message"]["subject"] == "add authenticate function"
    (repo / "truemsg.toml").write_text('fail_on = "warn"\n')
    assert cli.main(["check", "--ref", second, "--title", "修复支付漏洞", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["verdict"] == "WARN"
    assert (
        cli.main(
            ["check", "--ref", second, "--title", "修复支付漏洞", "--json", "--fail-on", "fail"]
        )
        == 0
    )
    capsys.readouterr()
    assert cli.main(["check", "--config", "missing.toml"]) == 2
    assert "Traceback" not in capsys.readouterr().err


def test_pr_uses_merge_base_and_explicit_range_is_respected(repo, capsys):
    first = commit_file(repo)
    git_command("checkout", "-b", "feature")
    commit_file(repo, "feature.py", "value = 1\n")
    git_command("checkout", "main")
    commit_file(repo, "main-only.py", "value = 2\n")
    assert (
        cli.main(
            [
                "check",
                "--pr",
                "--base",
                "main",
                "--head",
                "feature",
                "--title",
                "chore: fixture",
                "--json",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert [f["path"] for f in result["changes"]] == ["feature.py"]
    assert (
        cli.main(
            ["check", "--pr", "--range", f"{first}..feature", "--title", "chore: fixture", "--json"]
        )
        == 0
    )
    assert len(json.loads(capsys.readouterr().out)["changes"]) == 1
    assert (
        cli.main(["check", "--pr", "--range", "main..feature", "--base", "main", "--title", "x"])
        == 2
    )
    capsys.readouterr()


def test_cli_error_modes_and_pre_push_failures(repo, capsys, monkeypatch):
    commit_file(repo)
    for args in [
        ["check", "--ref", "HEAD", "--range", "HEAD..HEAD"],
        ["check", "--base", "HEAD"],
        ["check", "--pr"],
        ["suggest", "--ref", "HEAD", "--range", "HEAD..HEAD"],
        ["check", "--ref=--output=bad"],
        ["check", "--range", "missing..HEAD"],
    ]:
        assert cli.main(args) == 2
        assert "Traceback" not in capsys.readouterr().err
    monkeypatch.setattr("sys.stdin", io.StringIO("invalid input\n"))
    assert cli.main(["_pre-push"]) == 2
    capsys.readouterr()
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert cli.main(["_pre-push"]) == 0


def test_json_and_console_do_not_interpret_markup_or_controls(repo, capsys):
    commit_file(repo)
    assert cli.main(["check", "--title", "chore: [red]fixture\x1b[2J", "--no-color"]) == 0
    output = capsys.readouterr().out
    assert "\x1b" not in output
    assert "[red]" in output
    assert "\\x1b" in output
