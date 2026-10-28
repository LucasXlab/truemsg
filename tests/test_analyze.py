from truemsg.analyze import analyze
from truemsg.diff import parse_diff
from truemsg.message import parse_message

CODE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index a..b 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -0,0 +1,3 @@
+def authenticate(token):
+    return True
+
"""

TEST_DIFF = """diff --git a/tests/test_auth.py b/tests/test_auth.py
index a..b 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -0,0 +1,2 @@
+def test_auth():
+    pass
"""

MANY_LINES = "\n".join(f"+    line_{i} = {i}" for i in range(60))
BIG_CODE_DIFF = (
    "diff --git a/src/big.py b/src/big.py\n"
    "index a..b 100644\n--- a/src/big.py\n+++ b/src/big.py\n"
    "@@ -0,0 +1,60 @@\n" + MANY_LINES + "\n"
)


def test_feat_with_only_tests_fails():
    msg = parse_message("feat: add login feature")
    files = parse_diff(TEST_DIFF)
    res = analyze(msg, files)
    assert res["verdict"] == "FAIL"
    assert any(f["rule"] == "trivial-change" for f in res["findings"])


def test_feat_with_real_code_passes():
    msg = parse_message("feat(auth): add authenticate function")
    files = parse_diff(CODE_DIFF)
    res = analyze(msg, files)
    assert res["verdict"] in ("PASS", "WARN")
    assert any(f["rule"] == "consistent" for f in res["findings"])


def test_docs_with_big_code_warns():
    msg = parse_message("docs: update guide")
    files = parse_diff(BIG_CODE_DIFF)
    res = analyze(msg, files)
    assert any(f["rule"] == "docs-with-code" for f in res["findings"])


def test_keyword_mismatch_warns():
    msg = parse_message("feat: refactor payment gateway")
    files = parse_diff(CODE_DIFF)  # only auth/login content
    res = analyze(msg, files)
    assert any(f["rule"] == "keyword-mismatch" for f in res["findings"])


def test_empty_diff_passes():
    msg = parse_message("chore: release")
    res = analyze(msg, [])
    assert res["verdict"] == "PASS"
