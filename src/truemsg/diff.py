"""Parse a unified git diff into per-file structured changes."""

from __future__ import annotations

import os
import re
from typing import Dict, List

TEST_RE = re.compile(r"(^|/)(tests?|spec|__tests__|fixtures)(/|$)", re.IGNORECASE)
DOC_PATH_RE = re.compile(r"(^|/)(docs?)(/|$)", re.IGNORECASE)
DOC_EXT_RE = re.compile(r"\.(md|rst|txt|adoc|mdx)$", re.IGNORECASE)

CONFIG_EXT = {
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".ini",
    ".cfg",
    ".env",
    ".npmrc",
    ".editorconfig",
    ".properties",
    ".gradle",
}
CONFIG_NAMES = {
    "makefile",
    "dockerfile",
    "procfile",
    ".gitignore",
    ".env",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".pre-commit-config.yaml",
}
GENERATED_NAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "cargo.lock",
    "go.sum",
    "composer.lock",
    "gemfile.lock",
    "pipfile.lock",
}
GENERATED_PATH_RE = re.compile(
    r"(^|/)(dist|build|out|coverage|node_modules|\.next|target|__pycache__)(/|$)",
    re.IGNORECASE,
)
MINIFIED_RE = re.compile(r"\.(min\.js|min\.css|map)$", re.IGNORECASE)

COMMENT_TOKENS = {
    ".py": "#",
    ".js": "//",
    ".jsx": "//",
    ".ts": "//",
    ".tsx": "//",
    ".go": "//",
    ".rs": "//",
    ".sh": "#",
    ".yml": "#",
    ".yaml": "#",
    ".toml": "#",
    ".rb": "#",
    ".php": "//",
    ".java": "//",
    ".kt": "//",
    ".c": "//",
    ".h": "//",
    ".cpp": "//",
    ".cc": "//",
    ".hpp": "//",
    ".swift": "//",
    ".cs": "//",
}

# Declaration keywords per language -> capture the following identifier.
DECL_KEYWORDS = {
    "py": ["def", "class", "async"],
    "js": ["function", "class", "const", "let", "var"],
    "ts": ["function", "class", "interface", "type", "enum", "const", "let", "var"],
    "go": ["func", "type", "struct"],
    "rs": ["fn", "struct", "enum", "trait", "impl", "type", "mod"],
    "java": ["class", "interface", "enum", "record"],
    "kt": ["fun", "class", "object", "interface", "val", "var"],
    "csharp": ["class", "interface", "struct", "enum", "record"],
    "c": ["struct", "enum", "union", "typedef"],
    "cpp": ["class", "struct", "enum", "union", "typedef", "namespace"],
    "swift": ["func", "class", "struct", "enum", "protocol", "extension"],
    "rb": ["def", "class", "module"],
    "php": ["function", "class", "interface", "trait"],
}
# Keywords that imply control flow / logic (used by heuristics).
LOGIC_KEYWORDS = (
    "if",
    "else",
    "elif",
    "for",
    "while",
    "switch",
    "return",
    "break",
    "continue",
    "throw",
    "await",
    "async",
    "match",
)

_EXT_LANG = {
    ".py": "py",
    ".js": "js",
    ".jsx": "js",
    ".ts": "ts",
    ".tsx": "ts",
    ".go": "go",
    ".rs": "rs",
    ".java": "java",
    ".kt": "kt",
    ".kts": "kt",
    ".cs": "csharp",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".hpp": "cpp",
    ".swift": "swift",
    ".rb": "rb",
    ".php": "php",
}


def lang_of(path: str) -> str:
    return _EXT_LANG.get(os.path.splitext(path)[1].lower(), "")


def _decl_re(lang: str):
    kws = DECL_KEYWORDS.get(lang)
    if not kws:
        return None
    return re.compile(r"\b(?:" + "|".join(kws) + r")\s+([A-Za-z_][A-Za-z0-9_]*)")


def _identifiers(lines: List[str], lang: str) -> List[str]:
    rx = _decl_re(lang)
    if rx is None:
        return []
    seen: List[str] = []
    for line in lines:
        for m in rx.finditer(line):
            name = m.group(1)
            if name not in seen:
                seen.append(name)
    return seen


def _comments_only(added: List[str], path: str) -> bool:
    if not added:
        return False
    token = COMMENT_TOKENS.get(os.path.splitext(path)[1].lower())
    for line in added:
        s = line.strip()
        if s == "":
            continue
        if token and s.startswith(token):
            continue
        return False
    return True


class DiffError(ValueError):
    """A patch could not be completely interpreted."""


def _decode_path(value: str, prefix: str = "") -> str:
    import ast

    if value.startswith('"'):
        try:
            value = ast.literal_eval(value)
            if not isinstance(value, str):
                raise ValueError
            try:
                value = value.encode("latin1").decode("utf-8", "surrogateescape")
            except UnicodeEncodeError:
                pass
        except (ValueError, SyntaxError) as exc:
            raise DiffError("Invalid quoted Git filename") from exc
    if prefix and value.startswith(prefix):
        value = value[len(prefix) :]
    return value


def _header_paths(header: str) -> tuple[str, str]:
    candidates = []
    for match in re.finditer(r' (?=(?:"?b/))', header):
        try:
            left = _decode_path(header[: match.start()], "a/")
            right = _decode_path(header[match.end() :], "b/")
        except DiffError:
            continue
        candidates.append((left, right))
    for left, right in candidates:
        if left == right:
            return left, right
    if len(candidates) == 1:
        return candidates[0]
    # Extended headers (rename from/to or ---/+++) will disambiguate renames.
    if candidates:
        return candidates[0]
    raise DiffError("Unsupported diff file header")


def parse_diff(diff_text: str) -> List[Dict]:
    files: List[Dict] = []
    current = None
    remaining = [0, 0]
    hunk = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")

    for line in diff_text.split("\n"):
        if line.startswith("diff --git "):
            if any(remaining):
                raise DiffError("Truncated diff hunk")
            old, path = _header_paths(line[len("diff --git ") :])
            current = {
                "path": path,
                "old_path": old,
                "added": [],
                "removed": [],
                "status": "modified",
                "binary": False,
                "mode_changed": False,
            }
            files.append(current)
        elif current is None:
            if line.strip():
                raise DiffError("Expected a Git unified diff")
        elif any(remaining):
            if line.startswith("+") and remaining[1]:
                current["added"].append(line[1:])
                remaining[1] -= 1
            elif line.startswith("-") and remaining[0]:
                current["removed"].append(line[1:])
                remaining[0] -= 1
            elif line.startswith(" ") and all(remaining):
                remaining[0] -= 1
                remaining[1] -= 1
            elif line.startswith("\\ No newline"):
                continue
            else:
                raise DiffError("Invalid or truncated unified diff hunk")
        elif line.startswith("@@"):
            match = hunk.match(line)
            if not match:
                raise DiffError("Unsupported combined or malformed diff hunk")
            remaining = [
                int(match[2] if match[2] is not None else 1),
                int(match[4] if match[4] is not None else 1),
            ]
        elif line.startswith("index "):
            match = re.search(r" ([0-7]{6})$", line)
            if match:
                current.setdefault("old_mode", match[1])
                current.setdefault("new_mode", match[1])
        elif line.startswith("new file mode "):
            current["status"] = "added"
            current["new_mode"] = line.rsplit(" ", 1)[1]
        elif line.startswith("deleted file mode "):
            current["status"] = "deleted"
            current["old_mode"] = line.rsplit(" ", 1)[1]
        elif line.startswith(("old mode ", "new mode ")):
            current["mode_changed"] = True
            current["old_mode" if line.startswith("old") else "new_mode"] = line.rsplit(" ", 1)[1]
        elif line.startswith("rename from "):
            current["old_path"] = _decode_path(line[len("rename from ") :])
            current["status"] = "renamed"
        elif line.startswith("rename to "):
            current["path"] = _decode_path(line[len("rename to ") :])
        elif line.startswith("Binary files "):
            current["binary"] = True
        elif line.startswith("GIT binary patch"):
            raise DiffError("Binary patch bodies are unsupported; use ordinary Git diff output")
        elif line.startswith("+++ "):
            value = line[4:].split("\t", 1)[0]
            if value == "/dev/null":
                current["status"] = "deleted"
            else:
                current["path"] = _decode_path(value, "b/")
        elif line.startswith("--- "):
            value = line[4:].split("\t", 1)[0]
            if value == "/dev/null":
                current["status"] = "added"
            else:
                current["old_path"] = _decode_path(value, "a/")
        elif line.startswith(("+", "-")):
            raise DiffError("Hunk content outside a hunk")
        elif line and not line.startswith(
            ("index ", "similarity index ", "dissimilarity index ", "\\ No newline")
        ):
            raise DiffError("Unsupported diff metadata")
    if any(remaining):
        raise DiffError("Truncated diff hunk")

    for f in files:
        path = f["path"] or f["old_path"] or ""
        f["path"] = path
        lang = lang_of(path)
        f["lang"] = lang
        low = path.lower()
        base = os.path.basename(low)
        f["is_test"] = bool(TEST_RE.search(path))
        f["is_doc"] = bool(DOC_EXT_RE.search(path)) or bool(DOC_PATH_RE.search(path))
        f["is_config"] = low.endswith(tuple(CONFIG_EXT)) or base in CONFIG_NAMES
        f["is_generated"] = (
            base in GENERATED_NAMES
            or bool(GENERATED_PATH_RE.search(path))
            or bool(MINIFIED_RE.search(path))
        )
        f["identifiers"] = _identifiers(f["added"], lang)
        f["removed_identifiers"] = _identifiers(f["removed"], lang)
        f["comments_only"] = _comments_only(f["added"] + f["removed"], path)
        f["added_count"] = len(f["added"])
        f["removed_count"] = len(f["removed"])
        f["is_trivial_file"] = bool(
            f["is_test"] or f["is_doc"] or f["is_generated"] or f["comments_only"]
        )
        f["content_supported"] = not (
            f["binary"]
            or f["mode_changed"]
            or f.get("new_mode") in {"120000", "160000"}
            or f.get("old_mode") in {"120000", "160000"}
        )
    return files
