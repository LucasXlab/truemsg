"""Limited, explainable lexical signals; never a semantic truth assessment."""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional

from .config import DEFAULTS, is_ignored
from .diff import LOGIC_KEYWORDS

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")


def _stem(tok: str) -> str:
    if len(tok) > 3 and tok.endswith("s"):
        return tok[:-1]
    return tok


def _match_token(keyword: str, tokens: set) -> bool:
    k = _stem(keyword)
    for t in tokens:
        ts = _stem(t)
        if k == ts or k in ts or ts in k:
            return True
    return False


def _path_tokens(files: List[Dict]) -> set:
    toks: set = set()
    for f in files:
        path = f.get("path") or ""
        stem = re.sub(r"\.[^.]+$", "", os.path.basename(path))
        for part in re.split(r"[_\-./]", stem):
            if len(part) >= 3:
                toks.add(part.lower())
        for comp in path.split("/"):
            if len(comp) >= 3:
                toks.add(comp.lower())
        for ident in f.get("identifiers", []) + f.get("removed_identifiers", []):
            toks.add(ident.lower())
    return toks


def _diff_tokens(files: List[Dict]) -> set:
    toks = _path_tokens(files)
    for f in files:
        for line in f.get("added", []) + f.get("removed", []):
            for w in _WORD_RE.findall(line):
                if len(w) >= 4:
                    toks.add(w.lower())
    return toks


def _overlap(keywords: List[str], toks: set):
    if not keywords:
        return 0.0, []
    matched = [k for k in keywords if _match_token(k, toks)]
    return len(matched) / len(keywords), matched


def _categories_present(files: List[Dict]) -> List[str]:
    cats = set()
    for f in files:
        if f.get("is_test"):
            cats.add("测试")
        if f.get("is_doc"):
            cats.add("文档")
        if f.get("is_config"):
            cats.add("配置")
        if f.get("is_generated"):
            cats.add("生成文件")
        if f.get("comments_only") and not f.get("is_doc"):
            cats.add("注释")
        if f.get("binary"):
            cats.add("二进制")
    return sorted(cats)


def _logic_line_count(files: List[Dict]) -> int:
    rx = re.compile(r"\b(" + "|".join(LOGIC_KEYWORDS) + r")\b")
    count = 0
    for f in files:
        if f.get("is_trivial_file"):
            continue
        for line in f.get("added", []) + f.get("removed", []):
            if rx.search(line):
                count += 1
    return count


def analyze(message: Dict, files: List[Dict], config: Optional[Dict] = None) -> Dict:
    cfg = config or DEFAULTS
    th = cfg.get("thresholds", DEFAULTS["thresholds"])
    ignore = cfg.get("ignore", [])
    files = [f for f in files if f.get("path") and not is_ignored(f["path"], ignore)]

    findings: List[Dict] = []
    total_added = sum(f.get("added_count", 0) for f in files)
    total_removed = sum(f.get("removed_count", 0) for f in files)
    non_trivial = [f for f in files if not f.get("is_trivial_file")]
    real_lines = sum(f.get("added_count", 0) + f.get("removed_count", 0) for f in non_trivial)
    trivial = bool(files) and all(f.get("is_trivial_file") for f in files)

    toks = _diff_tokens(files)
    ratio, matched = _overlap(message.get("keywords", []), toks)
    missing = [k for k in message.get("keywords", []) if k not in matched]

    msg_type = message.get("type")
    scope = message.get("scope")
    subject = message.get("subject", "")
    subject_words = len(_WORD_RE.findall(subject))

    if not files:
        findings.append(
            {
                "level": "info",
                "rule": "empty",
                "title": "未检测到代码改动",
                "detail": "该范围没有 diff（可能是空提交、范围选错或被 ignore 过滤）。",
            }
        )
        return {
            "verdict": "PASS",
            "score": 100,
            "findings": findings,
            "summary": {"files": 0, "added": 0, "removed": 0, "real_lines": 0, "overlap": 1.0},
        }

    unsupported = [f for f in files if not f.get("content_supported", True)]
    if unsupported:
        findings.append(
            {
                "level": "warn",
                "rule": "insufficient-content",
                "title": "Content comparison is incomplete",
                "detail": "Binary, mode, symlink or submodule changes require manual review.",
            }
        )
    if not message.get("keywords"):
        findings.append(
            {
                "level": "warn",
                "rule": "insufficient-keywords",
                "title": "Insufficient lexical evidence",
                "detail": "No supported ASCII keywords; non-English messages require manual review.",
            }
        )

    # R1: limited path/comment-category signal, not proof of behaviour
    if msg_type in {"feat", "fix", "perf"} and trivial:
        cats = _categories_present(files)
        level = "fail" if msg_type in {"feat", "perf"} else "warn"
        findings.append(
            {
                "level": level,
                "rule": "trivial-change",
                "title": f"声称「{msg_type}」改动，但仅涉及：{', '.join(cats) or '注释/空白'}",
                "detail": "仅发现文档、测试、生成路径或注释信号；这不是无行为变化的证明，请人工复核。",
            }
        )

    # R2: docs commit that ships substantial code
    if msg_type == "docs" and real_lines > th["docs_with_code_lines"]:
        findings.append(
            {
                "level": "warn",
                "rule": "docs-with-code",
                "title": "docs 提交却包含大量实质代码改动",
                "detail": f"检测到约 {real_lines} 行非文档代码改动，考虑拆分提交。",
            }
        )

    # R3: message keywords not reflected in the diff
    if (
        not trivial
        and len(message.get("keywords", [])) >= th["min_keywords_for_overlap"]
        and ratio < th["overlap_low"]
    ):
        findings.append(
            {
                "level": "warn",
                "rule": "keyword-mismatch",
                "title": "提交信息关键词与代码改动缺乏对应",
                "detail": "信息里的关键词在 diff 中几乎找不到对应："
                + (", ".join(missing[:8]) or "（无）"),
            }
        )

    # R4: breaking change marker without any deletion
    if message.get("breaking") and not any(f.get("removed_identifiers") for f in files):
        findings.append(
            {
                "level": "warn",
                "rule": "breaking-no-deletion",
                "title": "标记破坏性变更，但未检测到删除/签名变更",
                "detail": "提交带 ! 或 BREAKING CHANGE，但 diff 里没有删除的标识符或签名变化。",
            }
        )

    # R5: huge diff, vague subject
    if (total_added + total_removed) > th["large_diff_lines"] and subject_words <= 3:
        findings.append(
            {
                "level": "warn",
                "rule": "vague-large",
                "title": "改动很大，但提交信息过于含糊",
                "detail": f"diff 共 {total_added + total_removed} 行，但标题只有 {subject_words} 个词：「{subject}」。",
            }
        )

    # R7: scope does not match any changed path/identifier
    if scope and not trivial:
        scope_toks = [t for t in re.split(r"[^A-Za-z0-9]+", scope.lower()) if t]
        if scope_toks and not any(_match_token(t, toks) for t in scope_toks):
            findings.append(
                {
                    "level": "warn",
                    "rule": "scope-mismatch",
                    "title": f"约定范围「{scope}」与改动路径不符",
                    "detail": "scope 里的关键词没有出现在任何改动文件路径或标识符中。",
                }
            )

    # R8: style commit that actually changes logic
    if msg_type == "style":
        logic = _logic_line_count(files)
        added_idents = sum(len(f.get("identifiers", [])) for f in files)
        if logic >= 3 or added_idents >= 1:
            findings.append(
                {
                    "level": "warn",
                    "rule": "style-with-logic",
                    "title": "style 提交却包含逻辑改动",
                    "detail": f"检测到约 {logic} 行含控制流、{added_idents} 个新标识符，可能应改为 fix/feat/refactor。",
                }
            )

    # R9: refactor without any identifier move/rename
    if msg_type == "refactor" and not trivial:
        if not any(f.get("identifiers") for f in files) and not any(
            f.get("removed_identifiers") for f in files
        ):
            findings.append(
                {
                    "level": "info",
                    "rule": "refactor-without-move",
                    "title": "refactor 提交没有移动/改名任何标识符",
                    "detail": "只有内容改动，没有新增或删除的函数/类——看起来更像普通修改而非重构。",
                }
            )

    # R6: positive signal
    if (
        not trivial
        and ratio >= th["overlap_high"]
        and message.get("is_conventional")
        and message.get("keywords")
        and not any(f["level"] in ("warn", "fail") for f in findings)
    ):
        findings.append(
            {
                "level": "info",
                "rule": "consistent",
                "title": "规则未发现词法冲突（需人工复核）",
                "detail": f"关键词重合 {ratio:.0%}；不证明语义一致或改动正确。",
            }
        )

    fails = [f for f in findings if f["level"] == "fail"]
    warns = [f for f in findings if f["level"] == "warn"]
    verdict = "FAIL" if fails else ("WARN" if warns else "PASS")
    score = max(0, 100 - 40 * len(fails) - 15 * len(warns))

    return {
        "verdict": verdict,
        "score": score,
        "findings": findings,
        "evidence": {
            "semantic_verified": False,
            "language": "ASCII keywords",
            "content_complete": not unsupported,
            "keywords_available": bool(message.get("keywords")),
        },
        "summary": {
            "files": len(files),
            "added": total_added,
            "removed": total_removed,
            "real_lines": real_lines,
            "overlap": round(ratio, 2),
        },
    }


def suggest_message(files: List[Dict]) -> Dict:
    """Heuristic, LLM-free commit message suggestion from a diff."""
    files = sorted((f for f in files if f.get("path")), key=lambda f: f["path"])
    if not files:
        return {
            "type": "chore",
            "scope": None,
            "subject": "update",
            "conventional": "chore: update",
        }

    non_trivial = [f for f in files if not f.get("is_trivial_file")]
    all_test = all(f.get("is_test") for f in files)
    all_doc = all(f.get("is_doc") for f in files)
    all_cfg = all(f.get("is_config") or f.get("is_generated") for f in files)

    if all_test:
        typ = "test"
    elif all_doc:
        typ = "docs"
    elif all_cfg:
        typ = "chore"
    elif not non_trivial:
        typ = "chore"
    else:
        # A declaration addition is observable; net line growth is not a feature detector.
        new_declarations = any(f.get("identifiers") for f in non_trivial)
        removed_declarations = any(f.get("removed_identifiers") for f in non_trivial)
        typ = "feat" if new_declarations and not removed_declarations else "chore"

    # scope: most common top-level dir among relevant files
    scope = None
    dirs = [os.path.dirname(f["path"]) for f in (non_trivial or files) if "/" in f["path"]]
    if dirs:
        top = [d.split("/")[0] for d in dirs]
        scope = min(set(top), key=lambda value: (-top.count(value), value))

    # subject
    added_idents = [i for f in non_trivial for i in f.get("identifiers", [])]
    test_idents = [i for f in files if f.get("is_test") for i in f.get("identifiers", [])]
    if added_idents and typ == "feat":
        subject = "add " + added_idents[0].lower()
    elif test_idents and typ == "test":
        name = test_idents[0]
        if name.lower().startswith("test_"):
            name = name[5:]
        subject = f"cover {name.lower()}" if name else "add coverage"
    else:
        stems = [
            re.sub(r"\.[^.]+$", "", os.path.basename(f["path"])) for f in (non_trivial or files)
        ]
        stem = min(set(stems), key=lambda value: (-stems.count(value), value)) if stems else "code"
        verb = {
            "feat": "add",
            "fix": "fix",
            "refactor": "refactor",
            "docs": "update",
            "test": "test",
            "chore": "update",
        }.get(typ, "update")
        subject = f"{verb} {stem.lower()}"

    conventional = f"{typ}({scope}): {subject}" if scope else f"{typ}: {subject}"
    return {
        "type": typ,
        "scope": scope,
        "subject": subject,
        "conventional": conventional,
        "requires_review": True,
        "basis": "changed paths and declarations; suggested type is provisional",
    }
