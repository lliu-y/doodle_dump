"""裁剪并标准化玩家提供的 PNG 素材。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "pixel_jump" / "assets"
COIN_SOURCE_DIR = ROOT / "resource" / "img"
MARIO_SHEET = COIN_SOURCE_DIR / "mario_and_items.png"
GAME_SIZE = (28, 32)
PREVIEW_SIZE = (56, 64)


def trim_alpha(image: Image.Image) -> Image.Image:
    """按可见像素裁掉透明边缘。"""
    image = image.convert("RGBA")
    bbox = image.getchannel("A").point(lambda alpha: 255 if alpha > 12 else 0).getbbox()
    if bbox is None:
        raise ValueError("素材没有可见像素")
    return image.crop(bbox)


def fit_sprite(image: Image.Image, resampling: Image.Resampling = Image.Resampling.NEAREST) -> Image.Image:
    """将角色等比例放入统一游戏画布，脚底对齐。"""
    image = trim_alpha(image)
    scale = min(26 / image.width, 30 / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    image = image.resize(size, resampling)
    canvas = Image.new("RGBA", GAME_SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(image, ((GAME_SIZE[0] - image.width) // 2, GAME_SIZE[1] - image.height))
    return canvas


def remove_connected_white_background(image: Image.Image) -> Image.Image:
    """只清除与画布边缘连通的白色背景，保留人物内部白色衣物。"""
    image = image.convert("RGB")
    marker = (1, 2, 3)
    marked = image.copy()
    ImageDraw.floodfill(marked, (0, 0), marker, thresh=28)
    mask = Image.eval(ImageChops.difference(marked, image).convert("L"), lambda value: 255 if value else 0)
    rgba = image.convert("RGBA")
    rgba.putalpha(ImageChops.invert(mask))
    return rgba


def make_mystery_sprite(source: Path) -> Image.Image:
    """去白底并裁出人物本体，排除地面阴影和右下角水印。"""
    original = Image.open(source).convert("RGB")
    foreground = remove_connected_white_background(original)
    # 人物主体在原图中央；裁切范围不包含底部阴影和右下角生成水印。
    body = foreground.crop((250, 150, 1490, 2180))
    body = trim_alpha(body)
    body.thumbnail((26, 30), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", GAME_SIZE, (0, 0, 0, 0))
    canvas.alpha_composite(body, ((GAME_SIZE[0] - body.width) // 2, GAME_SIZE[1] - body.height))
    return canvas


def save_character(name: str, sprite: Image.Image) -> None:
    """保存统一尺寸的游戏图与两倍预览图。"""
    sprite.save(ASSETS / f"{name}.png")
    preview = sprite.resize(PREVIEW_SIZE, Image.Resampling.NEAREST)
    preview.save(ASSETS / f"{name}_preview.png")


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    coin_source = next(
        (path for path in COIN_SOURCE_DIR.glob("*.png") if Image.open(path).size == (28, 32)),
        None,
    )
    if coin_source is None:
        raise FileNotFoundError(f"未找到金币源图：{COIN_SOURCE_DIR}")
    coin = trim_alpha(Image.open(coin_source))
    coin.thumbnail((14, 16), Image.Resampling.LANCZOS)
    coin_canvas = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    coin_canvas.alpha_composite(coin, ((16 - coin.width) // 2, (16 - coin.height) // 2))
    coin_canvas.save(ASSETS / "coin.png")

    mario_sheet = Image.open(MARIO_SHEET).convert("RGBA")
    mario_rows = ((0, 2, 18, 36), (0, 38, 18, 72), (0, 73, 16, 91))
    for index, box in enumerate(mario_rows, start=1):
        source = mario_sheet.crop(box)
        save_character(f"mario_type{index}", fit_sprite(source))

    mystery_source = next(ASSETS.glob("神秘玩家.png"))
    save_character("mystery_player", make_mystery_sprite(mystery_source))

    lizenian_source = next(ASSETS.glob("小小李泽念.png"))
    lizenian = fit_sprite(Image.open(lizenian_source), Image.Resampling.LANCZOS)
    save_character("little_lizenian", lizenian)

    print("金币: 16x16")
    for name in ("mario_type1", "mario_type2", "mario_type3", "mystery_player", "little_lizenian"):
        game_image = Image.open(ASSETS / f"{name}.png")
        preview = Image.open(ASSETS / f"{name}_preview.png")
        print(f"{name}: game={game_image.size}, preview={preview.size}")


if __name__ == "__main__":
    main()
