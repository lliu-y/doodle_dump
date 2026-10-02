"""协调游戏状态、输入、实体更新与各功能模块。"""

from __future__ import annotations

import random

import pygame

from .assets import load_images
from .audio import AudioManager
from .config import (
    AUDIO_DIR,
    BOUNCE_SPEED,
    CHARACTER_KEYS,
    CHARACTER_NEXT_RECT,
    CHARACTER_PREV_RECT,
    FPS,
    GRAVITY,
    HEIGHT,
    MOVE_SPEED,
    PLATFORM_GAP,
    PLAYER_SIZE,
    START_BUTTON_RECT,
    WIDTH,
)
from .entities import Cloud, Collectible, Platform
from .records import load_best_score, save_best_score
from .ui import GameView, UserInterface


class Game:
    """管理菜单、游戏中和结束状态，并调用专门模块完成工作。"""

    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
        except pygame.error:
            # 音频设备不可用时仍可运行静音游戏。
            pass

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("像素弹跳 - Pixel Jump")
        self.clock = pygame.time.Clock()

        # 各管理器只创建一次，整局游戏共享加载后的图片和音效。
        self.images = load_images()
        self.ui = UserInterface()
        self.audio = AudioManager(AUDIO_DIR)
        self.audio.play_track(self.audio.load_track)

        self.character_index = 0
        self.clouds = [
            Cloud(self.images["cloud"], -30.0, 72, 0.45),
            Cloud(self.images["cloud_small"], 310.0, 42, -0.32),
            Cloud(self.images["cloud_small"], 35.0, 575, 0.26),
            Cloud(self.images["cloud"], 400.0, 625, -0.38),
        ]
        self.state = "menu"
        self.best_score = load_best_score()
        self.reset()
        # reset() 建立一局初始状态，首次启动仍显示角色选择菜单。
        self.state = "menu"

    @property
    def character_key(self) -> str:
        """当前角色使用的图片资源键。"""
        return CHARACTER_KEYS[self.character_index]

    @property
    def score(self) -> int:
        """按本局最高高度计分，并加上拾取金币奖励。"""
        return int(self.max_height // 10) + self.score_bonus

    def reset(self) -> None:
        """建立新一局的玩家、平台、金币和计分状态。"""
        self.player = pygame.Rect(WIDTH // 2 - PLAYER_SIZE[0] // 2, HEIGHT - 150, *PLAYER_SIZE)
        self.player_y = float(self.player.y)
        self.start_y = self.player_y
        self.velocity_y = BOUNCE_SPEED
        self.camera_y = 0.0
        self.max_height = 0.0
        self.score_bonus = 0

        platform_image = self.images["platform"]
        self.platforms = [Platform(WIDTH // 2 - 34, HEIGHT - 105, platform_image)]
        y = HEIGHT - 190
        while y > -300:
            self.platforms.append(Platform(random.randint(20, WIDTH - 88), y, platform_image))
            y -= PLATFORM_GAP

        # 一局一枚金币，拾取后移除并奖励 100 分。
        self.collectible = Collectible(
            self.images["coin"],
            random.randint(40, WIDTH - 56),
            HEIGHT - 350,
        )
        self.state = "playing"

    def cycle_character(self, direction: int) -> None:
        """在开始游戏前循环选择角色。"""
        self.character_index = (self.character_index + direction) % len(CHARACTER_KEYS)

    def play_sound(self, sound: pygame.mixer.Sound | None) -> None:
        """由音频管理器播放已加载的音效。"""
        self.audio.play_sound(sound)

    def update_music(self) -> None:
        """让音频管理器按游戏状态维护背景音乐。"""
        self.audio.update(self.state)

    def update_clouds(self) -> None:
        """更新云层实体的位置。"""
        for cloud in self.clouds:
            cloud.update()

    def update(self) -> None:
        """更新玩家物理、平台碰撞、镜头、分数和结束状态。"""
        if self.state != "playing":
            return

        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(
            keys[pygame.K_LEFT] or keys[pygame.K_a]
        )
        self.player.x += round(direction * MOVE_SPEED)

        # 玩家离开屏幕一侧后从另一侧进入。
        if self.player.right < 0:
            self.player.left = WIDTH
        elif self.player.left > WIDTH:
            self.player.right = 0

        previous_bottom = self.player.bottom
        self.velocity_y += GRAVITY
        self.player_y += self.velocity_y
        self.player.y = round(self.player_y)

        # 只有向下穿过平台顶面时才触发自动弹跳。
        if self.velocity_y > 0:
            for platform in self.platforms:
                platform_screen = platform.screen_rect(self.camera_y)
                if (
                    previous_bottom <= platform_screen.top + 3
                    and self.player.bottom >= platform_screen.top
                    and self.player.right > platform.rect.left
                    and self.player.left < platform.rect.right
                ):
                    self.player_y = float(platform_screen.top - PLAYER_SIZE[1])
                    self.player.y = round(self.player_y)
                    self.velocity_y = BOUNCE_SPEED
                    self.play_sound(self.audio.bounce_sound)
                    break

        # 玩家到达画面上方后移动镜头，平台世界坐标不变。
        if self.player.top < HEIGHT * 0.38:
            shift = HEIGHT * 0.38 - self.player.top
            self.camera_y += shift
            self.player_y += shift
            self.player.y = round(self.player_y)

        current_height = self.start_y - self.player_y + self.camera_y
        self.max_height = max(self.max_height, current_height)

        # 清理离开屏幕底部的平台，并只在顶部需要时补充新平台。
        self.platforms = [
            platform
            for platform in self.platforms
            if platform.screen_rect(self.camera_y).top < HEIGHT + 40
        ]
        while min(
            (platform.screen_rect(self.camera_y).top for platform in self.platforms),
            default=HEIGHT,
        ) > -100:
            top_y = min(
                (platform.rect.y for platform in self.platforms),
                default=self.camera_y,
            ) - PLATFORM_GAP
            self.platforms.append(
                Platform(random.randint(16, WIDTH - 84), top_y, self.images["platform"])
            )

        if self.collectible is not None:
            if self.player.colliderect(self.collectible.screen_rect(self.camera_y)):
                self.collectible = None
                self.score_bonus += 100
                self.play_sound(self.audio.pickup_sound)

        if self.player.top > HEIGHT:
            self._finish_round()

    def _finish_round(self) -> None:
        """结束当前回合、播放死亡音效并保存新纪录。"""
        self.state = "over"
        self.audio.stop_track()
        self.play_sound(self.audio.death_sound)
        if self.score > self.best_score:
            self.best_score = self.score
            save_best_score(self.best_score)

    def draw(self) -> None:
        """将当前状态交给界面模块绘制。"""
        view = GameView(
            state=self.state,
            character_index=self.character_index,
            player=self.player,
            platforms=tuple(self.platforms),
            collectible=self.collectible,
            camera_y=self.camera_y,
            score=self.score,
            best_score=self.best_score,
        )
        self.ui.draw(self.screen, self.images, self.clouds, view)

    def _start_round(self) -> None:
        """开始或重新开始，并切换到游戏背景音乐。"""
        self.reset()
        self.audio.play_track(self.audio.game_track, loop=True)

    def _handle_event(self, event: pygame.event.Event) -> bool:
        """处理一个输入事件；返回 False 表示请求退出游戏。"""
        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.audio.music_enabled = not self.audio.music_enabled
            elif event.key == pygame.K_n:
                self.audio.sound_enabled = not self.audio.sound_enabled
            elif self.state == "menu" and event.key in (pygame.K_LEFT, pygame.K_a):
                self.cycle_character(-1)
            elif self.state == "menu" and event.key in (pygame.K_RIGHT, pygame.K_d):
                self.cycle_character(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.state in ("menu", "over"):
                    self._start_round()
            elif event.key == pygame.K_ESCAPE and self.state == "over":
                self.state = "menu"
                self.audio.play_track(self.audio.load_track)
            return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "menu":
                if CHARACTER_PREV_RECT.collidepoint(event.pos):
                    self.cycle_character(-1)
                elif CHARACTER_NEXT_RECT.collidepoint(event.pos):
                    self.cycle_character(1)
                elif START_BUTTON_RECT.collidepoint(event.pos):
                    self._start_round()
            elif self.state == "over":
                self._start_round()
        return True

    def run(self) -> None:
        """运行固定帧率主循环并持续处理窗口事件。"""
        running = True
        while running:
            self.clock.tick(FPS)
            self.update_clouds()
            self.update_music()
            for event in pygame.event.get():
                if not self._handle_event(event):
                    running = False
            self.update()
            self.draw()
        pygame.quit()


def main() -> None:
    """保持 `python -m pixel_jump` 使用的启动入口。"""
    Game().run()


if __name__ == "__main__":
    main()
