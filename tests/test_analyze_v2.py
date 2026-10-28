from truemsg.analyze import analyze
from truemsg.diff import parse_diff
from truemsg.message import parse_message


def _d(path, *lines):
    body = "\n".join(f"+{ln}" for ln in lines)
    return (
        f"diff --git a/{path} b/{path}\nindex a..b 100644\n"
        f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1,{len(lines)} @@\n{body}\n"
    )


def test_scope_mismatch_warns():
    diff = _d("src/billing.py", "def charge(card):", "    return True")
    msg = parse_message("feat(auth): add charge method")
    res = analyze(msg, parse_diff(diff))
    assert any(f["rule"] == "scope-mismatch" for f in res["findings"])


def test_style_with_logic_warns():
    diff = _d(
        "src/calc.py",
        "def compute(x):",
        "    if x > 0:",
        "        for i in range(x):",
        "            return i",
        "    return 0",
    )
    msg = parse_message("style: reformat compute")
    res = analyze(msg, parse_diff(diff))
    assert any(f["rule"] == "style-with-logic" for f in res["findings"])


def test_refactor_without_move_info():
    diff = _d("src/model.py", "    value = value + 1", "    value = value * 2")
    msg = parse_message("refactor: adjust value")
    res = analyze(msg, parse_diff(diff))
    assert any(f["rule"] == "refactor-without-move" for f in res["findings"])


def test_generated_files_count_as_trivial():
    diff = _d("dist/bundle.min.js", "var a=1;", "var b=2;")
    msg = parse_message("feat: add awesome feature")
    res = analyze(msg, parse_diff(diff))
    # only generated files -> trivial -> fail for feat
    assert res["verdict"] == "FAIL"
    assert any(f["rule"] == "trivial-change" for f in res["findings"])


def test_ignore_paths_via_config():
    diff = _d("generated/schema.go", "func Generate() {}")
    cfg = {"thresholds": {}, "ignore": ["generated/*"]}
    msg = parse_message("feat: add generator")
    res = analyze(msg, parse_diff(diff), config=cfg)
    assert res["verdict"] == "PASS"
    assert res["summary"]["files"] == 0
