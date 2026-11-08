"""Render analysis results for humans (rich) and machines (JSON)."""

from __future__ import annotations

import json
import re
from typing import Dict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

_LEVEL_COLOR = {"fail": "red", "warn": "yellow", "info": "green"}
_LEVEL_ICON = {"fail": "✗", "warn": "!", "info": "✓"}


def render_json(analysis: Dict, message: Dict, files: list) -> str:
    return json.dumps(
        {
            "verdict": analysis["verdict"],
            "score": analysis["score"],
            "summary": analysis["summary"],
            "message": {
                "type": message.get("type"),
                "subject": message.get("subject"),
                "breaking": message.get("breaking"),
            },
            "findings": analysis["findings"],
            "evidence": analysis.get("evidence", {"semantic_verified": False}),
            "changes": [
                {
                    key: item.get(key)
                    for key in (
                        "path",
                        "old_path",
                        "status",
                        "binary",
                        "mode_changed",
                        "content_supported",
                        "added_count",
                        "removed_count",
                    )
                }
                for item in files
            ],
        },
        ensure_ascii=True,
        indent=2,
    )


def _visible(value: str) -> str:
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", lambda m: f"\\x{ord(m[0]):02x}", value)


def render_console(
    console: Console,
    analysis: Dict,
    message: Dict,
    files: list,
    color: bool = True,
    language: str = "en",
) -> None:
    def t(english, chinese):
        return chinese if language == "zh-CN" else english

    verdict = analysis["verdict"]
    vcolor = {"PASS": "green", "WARN": "yellow", "FAIL": "red"}[verdict]

    header = Text()
    header.append("truemsg ", style="bold cyan")
    header.append(
        f"→ {verdict} ",
        style=f"bold {vcolor}",
    )
    score = analysis["score"] if analysis["score"] is not None else t("N/A", "不适用")
    header.append(
        t(f"(rule score {score}; not semantic proof)", f"(规则评分 {score}；非语义证明)"),
        style="dim",
    )
    console.print(header)

    meta = Table(show_header=False, box=None, padding=(0, 2))
    subj = message.get("subject") or t("(no subject)", "(无标题)")
    typ = message.get("type") or t("non-conventional", "非约定式")
    meta.add_row(t("Subject", "标题"), Text(_visible(subj)))
    meta.add_row(t("Type", "类型"), Text(_visible(typ) + (" !" if message.get("breaking") else "")))
    meta.add_row(
        t("Changes", "改动"),
        t(
            f"{analysis['summary']['files']} files, "
            f"+{analysis['summary']['added']}/-{analysis['summary']['removed']} lines, "
            f"keyword overlap {analysis['summary']['overlap']:.0%}",
            f"{analysis['summary']['files']} 文件, "
            f"+{analysis['summary']['added']}/-{analysis['summary']['removed']} 行, "
            f"关键词匹配 {analysis['summary']['overlap']:.0%}",
        ),
    )
    console.print(meta)

    if not analysis["findings"]:
        console.print(
            t(
                "  [green]✓ No rule conflict found; human review required[/green]",
                "  [green]✓ 规则未发现冲突；仍需人工复核[/green]",
            )
        )
        return

    for f in analysis["findings"]:
        color_name = _LEVEL_COLOR.get(f["level"], "white")
        icon = _LEVEL_ICON.get(f["level"], "·")
        line = Text()
        line.append(f"  {icon} ", style=f"bold {color_name}")
        line.append(_visible(f["title"]), style=f"bold {color_name}")
        console.print(line)
        if f.get("detail"):
            console.print(Text("    " + _visible(f["detail"]), style="dim"))

    console.print(
        Panel(
            t(
                "Limited lexical rules: PASS is not semantic proof; review WARN/FAIL findings manually.",
                "提示：这是有限词法规则；PASS 不证明语义一致，WARN/FAIL 也需要人工复核。",
            ),
            border_style="dim",
            expand=False,
        )
    )
