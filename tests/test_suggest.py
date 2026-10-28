from truemsg.analyze import suggest_message
from truemsg.diff import parse_diff


def _d(path, *lines):
    body = "\n".join(f"+{ln}" for ln in lines)
    return (
        f"diff --git a/{path} b/{path}\nindex a..b 100644\n"
        f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n{body}\n"
    )


def test_suggest_test_only():
    diff = _d("tests/test_x.py", "def test_x():", "    pass")
    s = suggest_message(parse_diff(diff))
    assert s["type"] == "test"


def test_suggest_feat():
    diff = _d("src/auth.py", "def authenticate(token):", "    return True")
    s = suggest_message(parse_diff(diff))
    assert s["type"] == "feat"
    assert "authenticate" in s["conventional"]


def test_suggest_docs():
    diff = _d("README.md", "# Title")
    s = suggest_message(parse_diff(diff))
    assert s["type"] == "docs"


def test_suggest_empty():
    s = suggest_message([])
    assert s["type"] == "chore"
