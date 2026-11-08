import io
import json
import re

import pytest
from rich.console import Console

from truemsg.analyze import analyze
from truemsg.cli import build_parser
from truemsg.diff import parse_diff
from truemsg.message import parse_message
from truemsg.report import render_console, render_json

PATCH = """diff --git a/tests/test_auth.py b/tests/test_auth.py
new file mode 100644
--- /dev/null
+++ b/tests/test_auth.py
@@ -0,0 +1,2 @@
+def test_auth():
+    pass
"""


def test_english_findings_and_console_are_english_by_default():
    message = parse_message("feat: add authentication")
    files = parse_diff(PATCH)
    result = analyze(message, files)
    out = io.StringIO()
    render_console(Console(file=out, width=160, no_color=True), result, message, files)
    assert result["verdict"] == "FAIL"
    assert "Subject" in out.getvalue()
    assert not re.search(r"[\u4e00-\u9fff]", out.getvalue())


def test_chinese_localizes_explanations_without_changing_rule_ids():
    message = parse_message("feat: add authentication")
    files = parse_diff(PATCH)
    english = analyze(message, files)
    chinese = analyze(message, files, language="zh-CN")
    payload = json.loads(render_json(chinese, message, files))
    assert [f["rule"] for f in english["findings"]] == [f["rule"] for f in payload["findings"]]
    assert "声称" in payload["findings"][0]["title"]
    assert english["summary"] == chinese["summary"]
    assert english["verdict"] == chinese["verdict"]
    assert build_parser().parse_args(["check", "--language", "zh-CN"]).language == "zh-CN"


@pytest.mark.parametrize("language", ["en", "zh-CN"])
def test_empty_comparison_renders_no_artificial_score(language):
    message = parse_message("chore: release")
    result = analyze(message, [], language=language)
    out = io.StringIO()
    render_console(Console(file=out, no_color=True), result, message, [], language=language)
    assert "100" not in out.getvalue()
    assert "WARN" in out.getvalue()
    assert json.loads(render_json(result, message, []))["score"] is None
