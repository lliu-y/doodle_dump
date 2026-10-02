"""游戏中的实体对象：平台、移动云层和奖励金币。"""

import pygame

from .config import WIDTH


class Platform:
    """可踩踏的平台；位置使用世界坐标，图片由资源管理器共享。"""

    def __init__(self, x: float, y: float, image: pygame.Surface):
        self.image = image
        self.rect = pygame.Rect(round(x), round(y), *image.get_size())

    def screen_rect(self, camera_y: float) -> pygame.Rect:
        """将世界坐标转换为屏幕坐标。"""
        return self.rect.move(0, round(camera_y))


class Cloud:
    """在背景上水平往返循环的云层。"""

    def __init__(self, image: pygame.Surface, x: float, y: int, speed: float):
        self.image = image
        self.x = x
        self.y = y
        self.speed = speed

    def update(self) -> None:
        """移动云朵，完全离开窗口后从另一侧重新进入。"""
        self.x += self.speed
        if self.speed > 0 and self.x > WIDTH:
            self.x = -self.image.get_width()
        elif self.speed < 0 and self.x + self.image.get_width() < 0:
            self.x = WIDTH

    def draw(self, surface: pygame.Surface) -> None:
        """绘制已加载的云图片。"""
        surface.blit(self.image, (round(self.x), self.y))


class Collectible:
    """可被玩家拾取的一枚金币奖励。"""

    def __init__(self, image: pygame.Surface, x: int, y: int):
        self.image = image
        self.rect = image.get_rect(topleft=(x, y))

    def screen_rect(self, camera_y: float) -> pygame.Rect:
        """把金币世界坐标转换到屏幕坐标。"""
        return self.rect.move(0, round(camera_y))
