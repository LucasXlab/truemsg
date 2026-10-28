"""Synthetic repositories; no personal Git configuration or network."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch, tmp_path):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_TERMINAL_PROMPT", "0")
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    monkeypatch.setenv("GIT_AUTHOR_NAME", "Synthetic Contributor")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "contributor@example.invalid")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "Synthetic Contributor")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "contributor@example.invalid")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    path = tmp_path / "repo"
    path.mkdir()
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True, capture_output=True)
    monkeypatch.chdir(path)
    return path


def git_command(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def commit_file(repo, path="src/example.py", text="value = 1\n", message="chore: initial fixture"):
    target = Path(repo) / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    git_command("add", "--", path)
    git_command("commit", "-m", message)
    return git_command("rev-parse", "HEAD")
