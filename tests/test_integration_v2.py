import os
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _run_truemsg(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.path.join(REPO_ROOT, "src")
    return subprocess.run(
        [sys.executable, "-m", "truemsg.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        env=env,
    )


def _make_repo():
    d = tempfile.mkdtemp()
    _git(["init"], d)
    _git(["config", "user.email", "contributor@example.invalid"], d)
    _git(["config", "user.name", "tester"], d)
    with open(os.path.join(d, "README.md"), "w") as fh:
        fh.write("# demo\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "docs: initial readme"], d)
    return d


def test_suggest_command():
    d = _make_repo()
    os.makedirs(os.path.join(d, "src"))
    with open(os.path.join(d, "src", "auth.py"), "w") as fh:
        fh.write("def authenticate(token):\n    return True\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat(auth): add authenticate function"], d)

    r = _run_truemsg(["suggest"], d)
    assert r.returncode == 0, r.stderr
    assert "feat" in r.stdout
    assert "authenticate" in r.stdout


def test_config_ignore_command(tmp_path=None):
    d = _make_repo()
    # commit the config first (chore), then the generated file alone
    with open(os.path.join(d, "truemsg.toml"), "w") as fh:
        fh.write('ignore = ["generated/*"]\n')
    _git(["add", "-A"], d)
    _git(["commit", "-m", "chore: add truemsg config"], d)

    os.makedirs(os.path.join(d, "generated"))
    with open(os.path.join(d, "generated", "schema.go"), "w") as fh:
        fh.write("package main\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat: add awesome feature"], d)

    r = _run_truemsg(["check"], d)
    assert r.returncode == 0, r.stdout  # ignored -> PASS, not FAIL
