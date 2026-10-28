import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import commit_file, git_command

from truemsg import git


def test_initial_commit_and_validated_ranges(repo):
    first = commit_file(repo)
    assert "+value = 1" in git.get_commit_diff()
    second = commit_file(repo, text="value = 2\n")
    assert "+value = 2" in git.get_diff(f"{first}..{second}")
    assert git.get_commit_message(first) == "chore: initial fixture"
    assert git.is_repo()
    assert git.repo_root() == str(repo)
    assert git.upstream_of() is None


@pytest.mark.parametrize("ref", ["--output=must-not-exist", "-cfoo=bar", "", "HEAD\n--ext-diff"])
def test_refs_cannot_be_options(repo, ref):
    commit_file(repo)
    with pytest.raises(git.GitError):
        git.resolve_ref(ref)
    assert not (repo / "must-not-exist").exists()


@pytest.mark.parametrize("spec", ["HEAD", "HEAD..", "..HEAD", "HEAD..HEAD..HEAD"])
def test_invalid_ranges_fail_closed(repo, spec):
    commit_file(repo)
    with pytest.raises(git.GitError):
        git.get_diff(spec)


def test_textconv_external_diff_and_format_config_are_disabled(repo, monkeypatch):
    first = commit_file(repo)
    marker = repo / "driver-ran"
    driver = repo / "driver.sh"
    driver.write_text(f"#!/bin/sh\nprintf unsafe > '{marker}'\ncat \"$1\"\n")
    driver.chmod(0o755)
    (repo / ".gitattributes").write_text("*.py diff=fixture\n")
    git_command("config", "diff.fixture.textconv", str(driver))
    git_command("config", "diff.external", str(driver))
    git_command("config", "color.ui", "always")
    git_command("config", "diff.noprefix", "true")
    monkeypatch.setenv("GIT_EXTERNAL_DIFF", str(driver))
    second = commit_file(repo, text="value = 2\n")
    patch = git.get_diff(f"{first}..{second}")
    assert "--- a/src/example.py" in patch
    assert "\x1b" not in patch
    assert not marker.exists()


def test_bounded_output_and_timeout(repo, monkeypatch):
    commit_file(repo)
    monkeypatch.setattr(git, "MAX_OUTPUT", 8)
    with pytest.raises(git.GitError, match="limit"):
        git.run_git(["log", "--format=%B"])
    monkeypatch.setattr(git, "MAX_OUTPUT", 8 * 1024 * 1024)
    original_popen = subprocess.Popen

    class ExpiringProcess(original_popen):
        def wait(self, timeout=None):
            if timeout is not None:
                raise subprocess.TimeoutExpired(self.args, timeout)
            return super().wait(timeout)

    monkeypatch.setattr(git.subprocess, "Popen", ExpiringProcess)
    with pytest.raises(git.GitError, match="time limit"):
        git.run_git(["log"])


def test_action_shell_treats_inputs_as_literal(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    stub = tmp_path / "truemsg"
    log = tmp_path / "args.json"
    stub.write_text(
        f"#!{sys.executable}\nimport json,sys\nopen({str(log)!r},'w').write(json.dumps(sys.argv[1:]))\n"
    )
    stub.chmod(0o755)
    marker = tmp_path / "never-created"
    payload = f'HEAD..$(touch "{marker}")'
    env = dict(
        os.environ,
        PATH=str(tmp_path) + os.pathsep + os.environ["PATH"],
        TRUEMSG_RANGE=payload,
        TRUEMSG_FAIL_ON="warn",
    )
    result = subprocess.run(
        ["bash", str(scripts / "action-check.sh")], env=env, capture_output=True
    )
    assert result.returncode == 0
    assert json.loads(log.read_text()) == ["check", "--range", payload, "--fail-on", "warn"]
    assert not marker.exists()
    env["TRUEMSG_FAIL_ON"] = "$(touch invalid)"
    assert (
        subprocess.run(
            ["bash", str(scripts / "action-check.sh")], env=env, capture_output=True
        ).returncode
        == 2
    )
    action = (scripts.parent / "action.yml").read_text()
    assert 'pip install "$GITHUB_ACTION_PATH"' in action
    assert 'RANGE="${{' not in action


def test_partial_clone_fails_before_any_object_fetch(repo):
    commit_file(repo)
    git_command("config", "remote.origin.promisor", "true")
    with pytest.raises(git.GitError, match="Partial/promisor"):
        git.resolve_ref("HEAD")


def test_relative_diff_configuration_cannot_hide_other_files(repo, monkeypatch):
    first = commit_file(repo, "outside.py", "value = 1\n")
    second = commit_file(repo, "outside.py", "value = 2\n")
    git_command("config", "diff.relative", "true")
    (repo / "nested").mkdir()
    monkeypatch.chdir(repo / "nested")
    assert "b/outside.py" in git.get_diff(f"{first}..{second}")


def test_log_signature_configuration_cannot_execute_gpg(repo):
    commit_file(repo)
    unsigned = git_command("cat-file", "commit", "HEAD")
    signed = unsigned.replace(
        "\n\n",
        "\ngpgsig -----BEGIN PGP SIGNATURE-----\n SYNTHETIC-NOT-A-SIGNATURE\n -----END PGP SIGNATURE-----\n\n",
        1,
    )
    oid = subprocess.check_output(
        ["git", "hash-object", "-t", "commit", "-w", "--stdin"], input=signed, text=True
    ).strip()
    marker = repo / "gpg-ran"
    helper = repo / "gpg-helper.sh"
    helper.write_text(f"#!/bin/sh\nprintf unsafe > '{marker}'\nexit 1\n")
    helper.chmod(0o755)
    git_command("config", "gpg.program", str(helper))
    git_command("config", "log.showSignature", "true")
    assert git.get_commit_message(oid) == "chore: initial fixture"
    assert not marker.exists()
