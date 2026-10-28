"""truemsg: offline commit/PR message <-> code consistency checker."""

__version__ = "0.2.0"

from .diff import parse_diff
from .git import get_commit_message, get_diff, is_repo, repo_root
from .message import parse_message

__all__ = [
    "parse_diff",
    "parse_message",
    "get_commit_message",
    "get_diff",
    "is_repo",
    "repo_root",
    "__version__",
]
