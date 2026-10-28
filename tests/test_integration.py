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


def test_real_feature_commit_passes():
    d = _make_repo()
    os.makedirs(os.path.join(d, "src"))
    with open(os.path.join(d, "src", "auth.py"), "w") as fh:
        fh.write("def authenticate(token):\n    return True\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat(auth): add authenticate function"], d)

    r = _run_truemsg(["check"], d)
    assert r.returncode == 0, r.stderr
    assert "PASS" in r.stdout


def test_lying_feat_commit_fails():
    d = _make_repo()
    os.makedirs(os.path.join(d, "tests"))
    with open(os.path.join(d, "tests", "test_x.py"), "w") as fh:
        fh.write("def test_x():\n    pass\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat: add awesome payment feature"], d)

    r = _run_truemsg(["check"], d)
    assert r.returncode == 1, r.stdout
    assert "FAIL" in r.stdout


def test_json_output():
    d = _make_repo()
    os.makedirs(os.path.join(d, "src"))
    with open(os.path.join(d, "src", "auth.py"), "w") as fh:
        fh.write("def authenticate(token):\n    return True\n")
    _git(["add", "-A"], d)
    _git(["commit", "-m", "feat(auth): add authenticate function"], d)

    r = _run_truemsg(["check", "--json"], d)
    assert r.returncode == 0
    assert '"verdict"' in r.stdout
    assert '"FAIL"' not in r.stdout


def test_hook_install():
    d = _make_repo()
    r = _run_truemsg(["hook", "--install"], d)
    assert r.returncode == 0, r.stderr
    assert os.path.exists(os.path.join(d, ".git", "hooks", "pre-push"))
