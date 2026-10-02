"""像素风自动弹跳平台跳跃游戏主程序。"""

from __future__ import annotations

import json
import math
import random
import struct
from pathlib import Path

import pygame

WIDTH, HEIGHT = 480, 720
FPS = 60
PLAYER_SIZE = (28, 32)
PLATFORM_SIZE = (68, 14)
GRAVITY = 0.38
BOUNCE_SPEED = -11.5
MOVE_SPEED = 5.0
PLATFORM_GAP = 82
SAVE_FILE = Path.home() / ".pixel_jump_record.json"

SKY = (20, 28, 52)
WHITE = (240, 244, 220)
GREEN = (104, 220, 126)
YELLOW = (255, 211, 92)
PINK = (249, 106, 142)


def make_tone(frequency: float, duration: float, volume: float = 0.18) -> pygame.mixer.Sound:
    """用标准库合成短音效，不依赖外部音频素材。"""
    sample_rate = 22050
    count = int(sample_rate * duration)
    samples = bytearray()
    for i in range(count):
        envelope = min(1.0, i / 180, (count - i) / 500)
        value = int(32767 * volume * max(0, envelope) * math.sin(2 * math.pi * frequency * i / sample_rate))
        samples.extend(struct.pack("<h", value))
    return pygame.mixer.Sound(buffer=bytes(samples))


def make_music() -> pygame.mixer.Sound:
    """合成一段可循环的简易像素风旋律。"""
    sample_rate = 22050
    notes = [523, 659, 784, 659, 587, 698, 880, 698, 523, 659, 784, 1047, 880, 784, 659, 587]
    note_length = 0.16
    raw = bytearray()
    for note in notes:
        size = int(sample_rate * note_length)
        for i in range(size):
            # 每个音符做极短淡入淡出，循环播放时减少爆音。
            edge = min(1.0, i / 220, (size - i) / 400)
            wave_value = math.sin(2 * math.pi * note * i / sample_rate)
            raw.extend(struct.pack("<h", int(32767 * 0.075 * max(0, edge) * wave_value)))
    return pygame.mixer.Sound(buffer=bytes(raw))


class Platform:
    """可踩踏的平台，位置使用世界坐标。"""

    def __init__(self, x: float, y: float, color: tuple[int, int, int] = GREEN):
        self.rect = pygame.Rect(round(x), round(y), *PLATFORM_SIZE)
        self.color = color

    def draw(self, surface: pygame.Surface, camera_y: float) -> None:
        rect = self.rect.move(0, -round(camera_y))
        pygame.draw.rect(surface, (15, 20, 38), rect.move(0, 4))
        pygame.draw.rect(surface, self.color, rect)
        pygame.draw.rect(surface, (195, 255, 178), (rect.x, rect.y, rect.width, 4))
        for x in range(rect.x + 8, rect.right - 4, 16):
            pygame.draw.rect(surface, (65, 151, 104), (x, rect.y + 7, 7, 3))


class Game:
    """管理游戏状态、物理更新、绘制与奖励规则。"""

    def __init__(self) -> None:
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1)
        except pygame.error:
            # 没有可用音频设备时仍允许游戏运行。
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("像素弹跳 - Pixel Jump")
        self.clock = pygame.time.Clock()
        self.font = self._font(22)
        self.small_font = self._font(16)
        self.title_font = self._font(42)
        self.state = "menu"
        self.music_on = True
        self.sound_on = True
        self.best_score = self.load_record()
        self.bounce_sound = make_tone(740, 0.08)
        self.pickup_sound = make_tone(1040, 0.14)
        self.music = make_music()
        if pygame.mixer.get_init():
            self.music.play(loops=-1)
        self.reset()

    @staticmethod
    def _font(size: int) -> pygame.font.Font:
        """优先使用常见中文字体，缺失时回退到系统默认字体。"""
        for name in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC"):
            try:
                return pygame.font.SysFont(name, size, bold=True)
            except (pygame.error, TypeError):
                continue
        return pygame.font.Font(None, size)

    @staticmethod
    def load_record() -> int:
        try:
            return int(json.loads(SAVE_FILE.read_text(encoding="utf-8")).get("best", 0))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return 0

    def save_record(self) -> None:
        try:
            SAVE_FILE.write_text(json.dumps({"best": self.best_score}), encoding="utf-8")
        except OSError:
            pass

    def reset(self) -> None:
        """开始新一局，保留最高纪录和音量开关。"""
        self.player = pygame.Rect(WIDTH // 2 - PLAYER_SIZE[0] // 2, HEIGHT - 150, *PLAYER_SIZE)
        self.player_y = float(self.player.y)
        self.velocity_y = BOUNCE_SPEED
        self.camera_y = 0.0
        self.max_height = 0.0
        self.score_bonus = 0
        self.platforms = [Platform(WIDTH // 2 - 34, HEIGHT - 105)]
        y = HEIGHT - 190
        while y > -300:
            self.platforms.append(Platform(random.randint(20, WIDTH - 88), y))
            y -= PLATFORM_GAP
        # 道具只增加分数，一局一个，便于初学者理解和实现。
        self.collectible = pygame.Rect(random.randint(40, WIDTH - 56), HEIGHT - 350, 16, 16)
        self.state = "playing"

    @property
    def score(self) -> int:
        return int(self.max_height // 10) + self.score_bonus

    def play_sound(self, sound: pygame.mixer.Sound) -> None:
        if self.sound_on and pygame.mixer.get_init():
            sound.play()

    def update_music(self) -> None:
        if not pygame.mixer.get_init():
            return
        if self.music_on and not pygame.mixer.get_busy():
            self.music.play(loops=-1)
        elif not self.music_on and pygame.mixer.get_busy():
            pygame.mixer.stop()

    def update(self) -> None:
        if self.state != "playing":
            return
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.player.x += round(direction * MOVE_SPEED)
        # 屏幕左右边缘相连，提供简单、直观的绕屏移动。
        if self.player.right < 0:
            self.player.left = WIDTH
        elif self.player.left > WIDTH:
            self.player.right = 0

        previous_bottom = self.player.bottom
        self.velocity_y += GRAVITY
        self.player_y += self.velocity_y
        self.player.y = round(self.player_y)

        # 只允许从平台上方下落时触发弹跳。
        if self.velocity_y > 0:
            for platform in self.platforms:
                screen_y = platform.rect.y - self.camera_y
                if (previous_bottom <= screen_y + 3 and self.player.bottom >= screen_y
                        and self.player.right > platform.rect.left
                        and self.player.left < platform.rect.right):
                    self.player_y = float(platform.rect.top - PLAYER_SIZE[1])
                    self.player.y = round(self.player_y)
                    self.velocity_y = BOUNCE_SPEED
                    self.play_sound(self.bounce_sound)
                    break

        # 玩家到达画面上方区域时向上滚屏，世界中的平台保持不动。
        if self.player.top < HEIGHT * 0.38:
            shift = HEIGHT * 0.38 - self.player.top
            self.camera_y += shift
            self.player_y += shift
            self.player.y = round(self.player_y)
            self.max_height += shift

        # 持续在顶部补充普通平台，并回收离开画面的平台。
        self.platforms = [p for p in self.platforms if p.rect.y - self.camera_y < HEIGHT + 40]
        while min((p.rect.y - self.camera_y for p in self.platforms), default=HEIGHT) > -100:
            top_y = min((p.rect.y for p in self.platforms), default=self.camera_y) - PLATFORM_GAP
            self.platforms.append(Platform(random.randint(16, WIDTH - 84), top_y))

        if self.collectible:
            item_screen = self.collectible.move(0, -round(self.camera_y))
            if self.player.colliderect(item_screen):
                self.collectible = None
                self.score_bonus += 100
                self.play_sound(self.pickup_sound)

        if self.player.top > HEIGHT:
            self.state = "over"
            if self.score > self.best_score:
                self.best_score = self.score
                self.save_record()

    def draw_background(self) -> None:
        self.screen.fill(SKY)
        # 离散像素星点随高度轻微视差移动，作为轻量背景装饰。
        for i in range(42):
            x = (i * 97 + 31) % WIDTH
            y = (i * 137 - int(self.camera_y * 0.18)) % HEIGHT
            pygame.draw.rect(self.screen, (49, 66, 94), (x, y, 3, 3))
        pygame.draw.rect(self.screen, (28, 39, 67), (0, HEIGHT - 22, WIDTH, 22))

    def draw_player(self) -> None:
        """用矩形像素块绘制精灵，避免外部图片素材依赖。"""
        x, y = self.player.x, self.player.y
        # 小精灵主体与像素五官。
        pygame.draw.rect(self.screen, (21, 25, 42), (x + 4, y + 2, 20, 27))
        pygame.draw.rect(self.screen, (255, 211, 92), (x + 4, y + 5, 20, 19))
        pygame.draw.rect(self.screen, (255, 239, 164), (x + 8, y, 12, 7))
        pygame.draw.rect(self.screen, (245, 125, 102), (x, y + 12, 7, 11))
        pygame.draw.rect(self.screen, (245, 125, 102), (x + 21, y + 12, 7, 11))
        pygame.draw.rect(self.screen, (49, 55, 79), (x + 9, y + 12, 3, 4))
        pygame.draw.rect(self.screen, (49, 55, 79), (x + 17, y + 12, 3, 4))
        pygame.draw.rect(self.screen, (121, 220, 136), (x + 5, y + 24, 8, 6))
        pygame.draw.rect(self.screen, (121, 220, 136), (x + 16, y + 24, 8, 6))

    def draw_collectible(self) -> None:
        if not self.collectible:
            return
        item = self.collectible.move(0, -round(self.camera_y))
        pygame.draw.rect(self.screen, (115, 72, 34), item.inflate(8, 8))
        pygame.draw.rect(self.screen, YELLOW, item)
        pygame.draw.rect(self.screen, WHITE, (item.x + 4, item.y + 4, 4, 4))

    def text(self, value: str, font: pygame.font.Font, center: tuple[int, int], color=WHITE) -> None:
        image = font.render(value, True, color)
        self.screen.blit(image, image.get_rect(center=center))

    def draw(self) -> None:
        self.draw_background()
        if self.state == "playing":
            for platform in self.platforms:
                platform.draw(self.screen, self.camera_y)
            self.draw_collectible()
            self.draw_player()
            self.text(f"分数 {self.score}", self.font, (75, 30))
            self.text(f"最高 {self.best_score}", self.small_font, (WIDTH - 65, 30))
            self.text("← → / A D 移动   M 音乐   N 音效", self.small_font, (WIDTH // 2, HEIGHT - 12), (175, 190, 207))
        elif self.state == "menu":
            self.text("像素弹跳", self.title_font, (WIDTH // 2, 210), YELLOW)
            self.text("踩住平台，向上跳得更高！", self.font, (WIDTH // 2, 275))
            self.draw_player()
            self.text("按 Enter 或点击屏幕开始", self.font, (WIDTH // 2, 420), GREEN)
            self.text("← → / A D 移动   M 音乐   N 音效", self.small_font, (WIDTH // 2, 470), (175, 190, 207))
            self.text(f"历史最高分：{self.best_score}", self.small_font, (WIDTH // 2, 520))
        else:
            self.text("游戏结束", self.title_font, (WIDTH // 2, 240), PINK)
            self.text(f"本局得分：{self.score}", self.font, (WIDTH // 2, 320))
            self.text(f"历史最高分：{self.best_score}", self.font, (WIDTH // 2, 365), YELLOW)
            self.text("按 Enter 或点击屏幕重新开始", self.font, (WIDTH // 2, 445), GREEN)
            self.text("按 Esc 返回主菜单", self.small_font, (WIDTH // 2, 490), WHITE)
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            self.update_music()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.music_on = not self.music_on
                    elif event.key == pygame.K_n:
                        self.sound_on = not self.sound_on
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.state in ("menu", "over"):
                            self.reset()
                    elif event.key == pygame.K_ESCAPE and self.state == "over":
                        self.state = "menu"
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state in ("menu", "over"):
                    self.reset()
            self.update()
            self.draw()
        pygame.quit()


def main() -> None:
    """游戏入口。"""
    Game().run()


if __name__ == "__main__":
    main()
