"""负责读取和保存本机历史最高分。"""

import json
from pathlib import Path

from .config import SAVE_FILE


def load_best_score(path: Path = SAVE_FILE) -> int:
    """读取最高分文件；文件不存在或内容异常时从 0 分开始。"""
    try:
        return max(0, int(json.loads(path.read_text(encoding="utf-8")).get("best", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_best_score(score: int, path: Path = SAVE_FILE) -> None:
    """将新的最高分写入用户目录。"""
    try:
        path.write_text(json.dumps({"best": score}), encoding="utf-8")
    except OSError:
        pass
