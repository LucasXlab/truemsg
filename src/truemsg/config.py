"""Validated TOML policy; unreadable or malformed explicit files fail closed."""

from __future__ import annotations

import copy
import fnmatch
import os
import stat
import tomllib
from typing import Dict, List

DEFAULTS: Dict = {
    "fail_on": "fail",
    "ignore": [],
    "thresholds": {
        "docs_with_code_lines": 40,
        "min_keywords_for_overlap": 2,
        "overlap_low": 0.34,
        "overlap_high": 0.6,
        "large_diff_lines": 200,
    },
}
MAX_CONFIG = 64 * 1024


class ConfigError(ValueError):
    """Invalid or unreadable configuration."""


def _merge(base: Dict, override: Dict) -> Dict:
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            _merge(base[key], val)
        else:
            base[key] = val
    return base


def _read_toml(path: str) -> Dict:
    try:
        flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as fh:
            info = os.fstat(fh.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CONFIG:
                raise ConfigError("Configuration must be a regular file of at most 64 KiB")
            payload = fh.read(MAX_CONFIG + 1)
            if len(payload) > MAX_CONFIG:
                raise ConfigError("Configuration exceeded 64 KiB")
            return tomllib.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError("Cannot read configuration as valid UTF-8 TOML") from exc


def _validate(cfg: Dict) -> None:
    if set(cfg) - set(DEFAULTS):
        raise ConfigError("Unknown configuration field")
    if not isinstance(cfg.get("fail_on"), str) or cfg["fail_on"] not in {"fail", "warn"}:
        raise ConfigError("fail_on must be fail or warn")
    patterns = cfg.get("ignore")
    if not isinstance(patterns, list) or not all(isinstance(x, str) for x in patterns):
        raise ConfigError("ignore must be an array of string globs")
    thresholds = cfg.get("thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) - set(DEFAULTS["thresholds"]):
        raise ConfigError("Unknown or invalid thresholds table")
    for key, value in thresholds.items():
        if key in {"overlap_low", "overlap_high"}:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise ConfigError("Overlap thresholds must be finite numbers between 0 and 1")
        elif isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ConfigError("Count thresholds must be nonnegative integers")
    if thresholds["min_keywords_for_overlap"] < 1:
        raise ConfigError("min_keywords_for_overlap must be positive")
    if thresholds["overlap_low"] > thresholds["overlap_high"]:
        raise ConfigError("overlap_low must not exceed overlap_high")


def load_config(config_path: str | None = None, start_dir: str = ".") -> Dict:
    cfg = copy.deepcopy(DEFAULTS)
    path = config_path or os.path.join(start_dir, "truemsg.toml")
    if config_path or os.path.lexists(path):
        override = _read_toml(path)
        _merge(cfg, override)
        _validate(cfg)
        cfg["_source"] = path
    return cfg


def is_ignored(path: str, patterns: List[str]) -> bool:
    norm = path.replace("\\", "/")
    return any(
        fnmatch.fnmatch(norm, pat.replace("\\", "/"))
        or fnmatch.fnmatch(os.path.basename(norm), pat.replace("\\", "/"))
        for pat in patterns or []
    )
