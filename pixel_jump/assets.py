"""负责将图片从磁盘加载一次，并提供给游戏各模块重复使用。"""

from pathlib import Path

import pygame

from .config import ASSET_DIR, CHARACTER_KEYS, CHARACTER_PREVIEW_KEYS

IMAGE_FILES = {
    "background": "background.png",
    "cloud": "cloud.png",
    "cloud_small": "cloud_small.png",
    "platform": "platform.png",
    "coin": "coin.png",
    **{key: f"{key}.png" for key in CHARACTER_KEYS},
    **{key: f"{key}.png" for key in CHARACTER_PREVIEW_KEYS},
}


def load_images(asset_dir: Path = ASSET_DIR) -> dict[str, pygame.Surface]:
    """加载并转换所有图片；背景不透明，其余图片保留透明像素。"""
    images = {}
    for key, filename in IMAGE_FILES.items():
        image = pygame.image.load(asset_dir / filename)
        images[key] = image.convert() if key == "background" else image.convert_alpha()
    return images
