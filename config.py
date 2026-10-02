"""集中保存窗口、物理、角色和素材目录等游戏配置。"""

from pathlib import Path

import pygame

WIDTH = 480
HEIGHT = 720
FPS = 60
PLAYER_SIZE = (28, 32)
GRAVITY = 0.38
BOUNCE_SPEED = -11.5
MOVE_SPEED = 5.0
PLATFORM_GAP = 82

PROJECT_DIR = Path(__file__).resolve().parent
ASSET_DIR = PROJECT_DIR / "assets"
AUDIO_DIR = ASSET_DIR / "audio"
SAVE_FILE = Path.home() / ".pixel_jump_record.json"

WHITE = (240, 244, 220)
GREEN = (104, 220, 126)
YELLOW = (255, 211, 92)
PINK = (249, 106, 142)
PROMPT_BLUE = (35, 76, 120)
HELP_BLUE = (68, 105, 145)
HELP_GRAY = (175, 190, 207)

CHARACTER_KEYS = (
    "player",
    "mario_type1",
    "mario_type2",
    "mario_type3",
    "mystery_player",
    "little_lizenian",
)
CHARACTER_PREVIEW_KEYS = tuple(f"{key}_preview" for key in CHARACTER_KEYS)
CHARACTER_NAMES = ("小精灵", "小马里奥", "中马里奥", "大马里奥", "神秘玩家", "小小李泽念")

CHARACTER_PREV_RECT = pygame.Rect(110, 278, 64, 64)
CHARACTER_NEXT_RECT = pygame.Rect(306, 278, 64, 64)
START_BUTTON_RECT = pygame.Rect(100, 380, 280, 60)
