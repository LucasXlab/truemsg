"""Parse a commit / PR message into structured, searchable pieces."""

from __future__ import annotations

import re
from typing import Dict, List

# Conventional commit types (https://www.conventionalcommits.org)
TYPES = {
    "feat": "新功能",
    "fix": "缺陷修复",
    "docs": "文档",
    "style": "格式（不影响逻辑）",
    "refactor": "重构",
    "perf": "性能",
    "test": "测试",
    "build": "构建/依赖",
    "ci": "CI",
    "chore": "杂务",
    "revert": "回滚",
}

CONV_RE = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)"
    r"(?P<scope>\([^)]*\))?"
    r"(?P<break>!)?"
    r":[ \t]*(?P<subject>.*)$",
    re.IGNORECASE,
)

# Words that carry no semantic signal for matching against code.
STOPWORDS = set(
    "a an the of to in on for and or with without is are be by from this that it its as at "
    "into via using use used new add adds added update updates updated remove removes removed "
    "fix fixes fixed change changes changed refactor make makes made implement support improve "
    "bump migrate handle allow enable disable set get code cleanup clean minor small various "
    "some stuff things wip todo just only also now when then them they we you i he she".split()
)

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]+")


def _keywords(text: str) -> List[str]:
    out: List[str] = []
    for raw in _TOKEN_RE.findall(text.lower()):
        tok = raw.strip("-_")
        if len(tok) < 3:
            continue
        if tok in STOPWORDS:
            continue
        out.append(tok)
    return out


def parse_message(text: str) -> Dict:
    lines = [ln for ln in text.strip().splitlines() if ln.strip() != ""]
    first_line = lines[0] if lines else ""
    body = "\n".join(lines[1:])

    match = CONV_RE.match(first_line)
    msg_type = None
    scope = None
    breaking = False
    subject = first_line

    if match:
        msg_type = match.group("type").lower()
        scope = match.group("scope")
        if scope:
            scope = scope[1:-1]
        breaking = bool(match.group("break"))
        subject = match.group("subject")

    if re.search(r"^\s*BREAKING CHANGE", text, re.MULTILINE | re.IGNORECASE):
        breaking = True

    keywords = _keywords(subject + " " + body)
    if scope:
        keywords = _keywords(scope) + keywords
    return {
        "raw": text,
        "type": msg_type,
        "type_label": TYPES.get(msg_type, "未知/非约定式"),
        "scope": scope,
        "breaking": breaking,
        "subject": subject,
        "body": body,
        "keywords": keywords,
        "is_conventional": match is not None,
    }
