"""Run the installed CLI on synthetic, disposable Git history."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="truemsg-demo-") as directory:
        root = Path(directory)
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

        def run(argv, expected=0):
            result = subprocess.run(
                argv, cwd=root, env=env, capture_output=True, text=True, timeout=30
            )
            if result.returncode != expected:
                raise RuntimeError(
                    f"Synthetic demo command failed: expected {expected}, got {result.returncode}"
                )
            return result.stdout

        run(["git", "init", "-b", "main"])
        (root / "README.md").write_text("# Synthetic demonstration\n")
        run(["git", "add", "README.md"])
        run(["git", "commit", "-m", "docs: initial readme"])
        (root / "src").mkdir()
        (root / "src/auth.py").write_text("def authenticate(token):\n    return True\n")
        run(["git", "add", "src/auth.py"])
        run(["git", "commit", "-m", "feat(auth): add authenticate function"])
        output = run([sys.executable, "-m", "truemsg.cli", "check", "--json"])
        good = json.loads(output)
        assert good["verdict"] == "PASS"
        print("$ truemsg check --json  # synthetic auth change")
        print(output.strip())
        (root / "tests").mkdir()
        (root / "tests/test_auth.py").write_text("def test_auth():\n    assert True\n")
        run(["git", "add", "tests/test_auth.py"])
        run(["git", "commit", "-m", "feat: add synthetic payment feature"])
        mismatch = run([sys.executable, "-m", "truemsg.cli", "check", "--json"], expected=1)
        assert json.loads(mismatch)["verdict"] == "FAIL"
        print("\n$ truemsg check --json  # tests-only change with a feature claim")
        print(mismatch.strip())
        print(
            "\nPASS means no rule conflict, not verified semantic consistency. Both fixtures are synthetic."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
