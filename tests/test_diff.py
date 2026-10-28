from truemsg.diff import parse_diff


def _diff(text):
    return parse_diff(text)


SAMPLE_CODE = """diff --git a/src/auth.py b/src/auth.py
index a..b 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -0,0 +1,3 @@
+def authenticate(token):
+    return True
+
"""

SAMPLE_TEST = """diff --git a/tests/test_auth.py b/tests/test_auth.py
index a..b 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -0,0 +1,2 @@
+def test_auth():
+    pass
"""

SAMPLE_DOC = """diff --git a/README.md b/README.md
index a..b 100644
--- a/README.md
+++ b/README.md
@@ -0,0 +1,1 @@
+# Title
"""


def test_code_file_classified():
    files = _diff(SAMPLE_CODE)
    assert len(files) == 1
    f = files[0]
    assert f["path"] == "src/auth.py"
    assert f["is_test"] is False
    assert f["is_doc"] is False
    assert f["identifiers"] == ["authenticate"]
    assert f["added_count"] == 3


def test_test_file_flagged():
    files = _diff(SAMPLE_TEST)
    assert files[0]["is_test"] is True


def test_doc_file_flagged():
    files = _diff(SAMPLE_DOC)
    assert files[0]["is_doc"] is True


def test_deleted_status():
    text = """diff --git a/old.py b/old.py
deleted file mode 100644
index a..b
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def gone():
-    pass
"""
    files = _diff(text)
    assert files[0]["status"] == "deleted"
    assert files[0]["removed_identifiers"] == ["gone"]
