"""负责字体、背景、实体及各游戏状态画面的渲染。"""

from dataclasses import dataclass
from typing import Mapping

import pygame

from config import (
    CHARACTER_KEYS,
    CHARACTER_NAMES,
    CHARACTER_PREVIEW_KEYS,
    CHARACTER_PREV_RECT,
    CHARACTER_NEXT_RECT,
    HELP_BLUE,
    HELP_GRAY,
    HEIGHT,
    PINK,
    PROMPT_BLUE,
    START_BUTTON_RECT,
    WHITE,
    WIDTH,
    YELLOW,
)
from entities import Cloud, Collectible, Platform


@dataclass(frozen=True)
class GameView:
    """提供给界面的只读状态，避免界面依赖整个游戏控制器。"""

    state: str
    character_index: int
    player: pygame.Rect
    platforms: tuple[Platform, ...]
    collectible: Collectible | None
    camera_y: float
    score: int
    best_score: int


class UserInterface:
    """保存预创建字体并按当前状态绘制界面。"""

    def __init__(self) -> None:
        self.font = self._font(22)
        self.small_font = self._font(16)
        self.title_font = self._font(42)

    @staticmethod
    def _font(size: int) -> pygame.font.Font:
        """优先使用常见中文字体，缺失时使用系统默认字体。"""
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC"):
            try:
                return pygame.font.SysFont(name, size, bold=True)
            except (pygame.error, TypeError):
                continue
        return pygame.font.Font(None, size)

    def _text(
        self,
        surface: pygame.Surface,
        value: str,
        font: pygame.font.Font,
        center: tuple[int, int],
        color=WHITE,
    ) -> None:
        """绘制单段居中文本。"""
        image = font.render(value, True, color)
        surface.blit(image, image.get_rect(center=center))

    @staticmethod
    def draw_background(
        surface: pygame.Surface,
        images: Mapping[str, pygame.Surface],
        clouds: tuple[Cloud, ...],
    ) -> None:
        """绘制天空背景和云层。"""
        surface.blit(images["background"], (0, 0))
        for cloud in clouds:
            cloud.draw(surface)

    def draw(
        self,
        surface: pygame.Surface,
        images: Mapping[str, pygame.Surface],
        clouds: tuple[Cloud, ...],
        view: GameView,
    ) -> None:
        """按菜单、游戏或结束状态绘制一帧。"""
        self.draw_background(surface, images, clouds)
        if view.state == "playing":
            self._draw_game(surface, images, view)
        elif view.state == "menu":
            self._draw_menu(surface, images, view)
        else:
            self._draw_game_over(surface, view)
        pygame.display.flip()

    def _draw_game(self, surface: pygame.Surface, images: dict, view: GameView) -> None:
        """绘制当前游戏画面与分数。"""
        for platform in view.platforms:
            surface.blit(platform.image, platform.screen_rect(view.camera_y))
        if view.collectible is not None:
            surface.blit(images["coin"], view.collectible.screen_rect(view.camera_y))
        surface.blit(images[CHARACTER_KEYS[view.character_index]], view.player)
        self._text(surface, f"分数 {view.score}", self.font, (75, 30))
        self._text(surface, f"最高 {view.best_score}", self.small_font, (WIDTH - 65, 30))
        self._text(
            surface,
            "← → / A D 移动   M 音乐   N 音效",
            self.small_font,
            (WIDTH // 2, HEIGHT - 12),
            HELP_GRAY,
        )

    def _draw_menu(self, surface: pygame.Surface, images: dict, view: GameView) -> None:
        """绘制角色选择与开始提示。"""
        self._text(surface, "像素弹跳", self.title_font, (WIDTH // 2, 145), YELLOW)
        self._text(surface, "踩住平台，向上跳得更高！", self.font, (WIDTH // 2, 205))
        self._text(surface, "选择角色", self.small_font, (WIDTH // 2, 260))
        self._text(surface, "‹", self.title_font, CHARACTER_PREV_RECT.center)
        self._text(surface, "›", self.title_font, CHARACTER_NEXT_RECT.center)
        preview = images[CHARACTER_PREVIEW_KEYS[view.character_index]]
        surface.blit(preview, preview.get_rect(center=(WIDTH // 2, 310)))
        self._text(surface, CHARACTER_NAMES[view.character_index], self.font, (WIDTH // 2, 360), YELLOW)
        self._text(surface, "Enter 开始游戏", self.font, START_BUTTON_RECT.center, PROMPT_BLUE)
        self._text(surface, "← → 选择角色   M 音乐   N 音效", self.small_font, (WIDTH // 2, 475), HELP_BLUE)
        self._text(surface, "游戏中用 ← → 或 A / D 移动", self.small_font, (WIDTH // 2, 505), HELP_BLUE)
        self._text(surface, f"历史最高分：{view.best_score}", self.small_font, (WIDTH // 2, 545), HELP_BLUE)

    def _draw_game_over(self, surface: pygame.Surface, view: GameView) -> None:
        """绘制结算分数与重开提示。"""
        self._text(surface, "游戏结束", self.title_font, (WIDTH // 2, 240), PINK)
        self._text(surface, f"本局得分：{view.score}", self.font, (WIDTH // 2, 320))
        self._text(surface, f"历史最高分：{view.best_score}", self.font, (WIDTH // 2, 365), YELLOW)
        self._text(surface, "按 Enter 或点击屏幕重新开始", self.font, (WIDTH // 2, 445), PROMPT_BLUE)
        self._text(surface, "按 Esc 返回主菜单", self.small_font, (WIDTH // 2, 490))
