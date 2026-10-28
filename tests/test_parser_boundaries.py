import pytest
from conftest import commit_file, git_command

from truemsg import git
from truemsg.analyze import analyze, suggest_message
from truemsg.diff import DiffError, parse_diff
from truemsg.message import parse_message


@pytest.mark.parametrize(
    "name",
    [
        "src/汉字.py",
        "src/with space.py",
        "src/a\tb.py",
        "src/a\nb.py",
        'src/a"b.py',
        "src/a\\b.py",
        "src/a b/inner.py",
    ],
)
def test_real_git_quoted_path_identity_and_hunk_prefix(repo, name):
    first = commit_file(repo, name, "-- old content\n")
    second = commit_file(repo, name, "++ new content\n")
    files = parse_diff(git.get_diff(f"{first}..{second}"))
    assert len(files) == 1
    assert files[0]["path"] == name
    assert files[0]["added"] == ["++ new content"]
    assert files[0]["removed"] == ["-- old content"]


def test_binary_mode_and_rename_are_not_empty(repo):
    first = commit_file(repo, "blob.bin", "initial\x00binary")
    commit_file(repo, text="return False\n")
    (repo / "blob.bin").write_bytes(b"changed\x00binary")
    (repo / "src/example.py").chmod(0o755)
    git_command("mv", "src/example.py", "src/renamed.py")
    git_command("add", "-A")
    git_command("commit", "-m", "chore: update metadata")
    files = parse_diff(git.get_diff(f"{first}..HEAD"))
    assert {f["path"] for f in files} == {"blob.bin", "src/renamed.py"}
    binary = next(f for f in files if f["path"] == "blob.bin")
    assert binary["binary"]
    result = analyze(parse_message("fix: repair binary"), [binary])
    assert result["summary"]["files"] == 1
    assert any(f["rule"] == "insufficient-content" for f in result["findings"])
    previous = git.resolve_ref("HEAD~1")
    rename = parse_diff(git.get_diff(f"{previous}..HEAD"))
    assert any(f["status"] == "renamed" and f["old_path"] == "src/example.py" for f in rename)
    assert any(f["mode_changed"] for f in rename)


def test_deleted_logic_is_not_comments_only(repo):
    first = commit_file(repo, text="return False\n")
    second = commit_file(repo, text="# removed return\n")
    file = parse_diff(git.get_diff(f"{first}..{second}"))[0]
    assert not file["comments_only"]
    assert not file["is_trivial_file"]
    result = analyze(parse_message("feat: change behavior"), [file])
    assert not any(f["rule"] == "trivial-change" for f in result["findings"])


def test_configuration_is_not_proof_of_no_behavior(repo):
    first = commit_file(repo, "settings.toml", "security = true\n")
    second = commit_file(repo, "settings.toml", "security = false\n")
    file = parse_diff(git.get_diff(f"{first}..{second}"))[0]
    assert file["is_config"] and not file["is_trivial_file"]


@pytest.mark.parametrize("message", ["修复支付漏洞", "fix: update the", ""])
def test_missing_keywords_never_claim_semantic_consistency(repo, message):
    commit_file(repo)
    result = analyze(parse_message(message), parse_diff(git.get_commit_diff()))
    assert result["verdict"] == "WARN"
    assert result["summary"]["overlap"] == 0
    assert not result["evidence"]["semantic_verified"]
    assert not any(f["rule"] == "consistent" for f in result["findings"])


def test_truncated_and_unsupported_patches_fail_closed():
    with pytest.raises(DiffError):
        parse_diff("not a patch")
    with pytest.raises(DiffError):
        parse_diff("diff --git a/a.py b/a.py\n@@ -0,0 +1,2 @@\n+only one\n")
    with pytest.raises(DiffError):
        parse_diff("diff --git a/a b/a\nGIT binary patch\n")


def test_suggestion_is_deterministic_and_does_not_use_net_growth():
    files = parse_diff(
        "diff --git a/z/x.py b/z/x.py\n@@ -0,0 +1 @@\n+value = 1\ndiff --git a/a/y.py b/a/y.py\n@@ -0,0 +1 @@\n+value = 2\n"
    )
    first = suggest_message(files)
    assert first == suggest_message(list(reversed(files)))
    assert first["type"] == "chore"
    assert first["scope"] == "a"
    assert first["requires_review"]
