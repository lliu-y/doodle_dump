"""离线生成游戏 PNG 素材；运行时由 game.py 加载生成后的图片。"""

from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


def make_background() -> pygame.Surface:
    """生成蓝天底图，云层由游戏单独加载并移动。"""
    image = pygame.Surface((480, 720))
    bands = [(105, 198, 246), (112, 203, 248), (121, 208, 250), (130, 212, 250)]
    for y in range(0, 720, 60):
        pygame.draw.rect(image, bands[(y // 60) % len(bands)], (0, y, 480, 60))
    pygame.draw.rect(image, (160, 224, 250), (0, 708, 480, 12))
    return image


def make_cloud() -> pygame.Surface:
    """生成有像素台阶轮廓的白云，透明区域可叠在天空上。"""
    image = pygame.Surface((96, 48), pygame.SRCALPHA)
    shadow = (199, 231, 246)
    white = (255, 255, 255)
    highlight = (255, 255, 255, 220)
    pygame.draw.rect(image, shadow, (8, 28, 80, 16))
    pygame.draw.rect(image, shadow, (16, 20, 24, 16))
    pygame.draw.rect(image, shadow, (32, 12, 32, 24))
    pygame.draw.rect(image, shadow, (56, 20, 24, 16))
    pygame.draw.rect(image, white, (8, 24, 80, 16))
    pygame.draw.rect(image, white, (16, 16, 24, 16))
    pygame.draw.rect(image, white, (32, 8, 32, 24))
    pygame.draw.rect(image, white, (56, 16, 24, 16))
    pygame.draw.rect(image, highlight, (24, 16, 12, 4))
    pygame.draw.rect(image, highlight, (40, 8, 16, 4))
    return image


def make_player() -> pygame.Surface:
    """用像素网格绘制小精灵并导出成静态精灵图。"""
    image = pygame.Surface((28, 32), pygame.SRCALPHA)
    grid = [
        "..HHH..",
        ".HHHHH.",
        "HMMMMMH",
        "HMMMMMH",
        "HMEEMMH",
        "HMMMMMH",
        "HMMOMMH",
        ".HMMMH.",
    ]
    colors = {
        "H": (48, 67, 104),
        "M": (255, 204, 99),
        "E": (39, 62, 91),
        "O": (231, 119, 111),
    }
    for row, line in enumerate(grid):
        for column, cell in enumerate(line):
            if cell != ".":
                pygame.draw.rect(image, colors[cell], (column * 4, row * 4, 4, 4))
    pygame.draw.rect(image, (114, 220, 139), (4, 28, 8, 4))
    pygame.draw.rect(image, (114, 220, 139), (16, 28, 8, 4))
    return image


def make_mario() -> pygame.Surface:
    """生成戴红帽、穿蓝背带裤的像素水管工角色。"""
    image = pygame.Surface((28, 32), pygame.SRCALPHA)
    grid = [
        "..rrr..",
        ".rrrrr.",
        "RRRRRRR",
        "..SSS..",
        ".SSMSS.",
        ".BBBBB.",
        ".BYYB..",
        "TT...TT",
    ]
    colors = {
        "R": (209, 48, 47),
        "r": (241, 76, 62),
        "S": (255, 191, 132),
        "M": (112, 62, 45),
        "B": (48, 96, 190),
        "Y": (255, 215, 85),
        "T": (124, 73, 51),
    }
    occupied = {
        (column, row)
        for row, line in enumerate(grid)
        for column, cell in enumerate(line)
        if cell != "."
    }
    for column, row in occupied:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = (column + dx, row + dy)
            if neighbor not in occupied and 0 <= neighbor[0] < 7 and 0 <= neighbor[1] < 8:
                pygame.draw.rect(image, (62, 48, 61), (neighbor[0] * 4, neighbor[1] * 4, 4, 4))
    for row, line in enumerate(grid):
        for column, cell in enumerate(line):
            if cell != ".":
                pygame.draw.rect(image, colors[cell], (column * 4, row * 4, 4, 4))
    return image


def make_platform() -> pygame.Surface:
    """生成 68x14 像素平台图片。"""
    image = pygame.Surface((68, 14), pygame.SRCALPHA)
    pygame.draw.rect(image, (54, 133, 98), (0, 4, 68, 10))
    pygame.draw.rect(image, (104, 220, 126), (0, 0, 68, 8))
    pygame.draw.rect(image, (202, 255, 177), (0, 0, 68, 3))
    for x in range(8, 64, 16):
        pygame.draw.rect(image, (69, 164, 110), (x, 5, 7, 3))
    return image


def make_coin() -> pygame.Surface:
    """生成金币奖励图片。"""
    image = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(image, (193, 121, 43), (4, 0, 8, 16))
    pygame.draw.rect(image, (255, 211, 92), (2, 2, 12, 12))
    pygame.draw.rect(image, (255, 240, 167), (5, 4, 4, 4))
    pygame.draw.rect(image, (255, 240, 167), (5, 10, 6, 2))
    return image


def main() -> None:
    pygame.init()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        "background.png": make_background(),
        "cloud.png": make_cloud(),
        "player.png": make_player(),
        "mario.png": make_mario(),
        "platform.png": make_platform(),
        "coin.png": make_coin(),
    }
    images["cloud_small.png"] = pygame.transform.scale(images["cloud.png"], (72, 36))
    images["player_preview.png"] = pygame.transform.scale(images["player.png"], (56, 64))
    images["mario_preview.png"] = pygame.transform.scale(images["mario.png"], (56, 64))
    for filename, image in images.items():
        pygame.image.save(image, ASSET_DIR / filename)
    pygame.quit()
    print(f"Generated {len(images)} PNG assets in {ASSET_DIR}")


if __name__ == "__main__":
    main()
