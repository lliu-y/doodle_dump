"""像素风自动弹跳平台跳跃游戏主程序。"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pygame

WIDTH, HEIGHT = 480, 720
FPS = 60
PLAYER_SIZE = (28, 32)
GRAVITY = 0.38
BOUNCE_SPEED = -11.5
MOVE_SPEED = 5.0
PLATFORM_GAP = 82
SAVE_FILE = Path.home() / ".pixel_jump_record.json"

WHITE = (240, 244, 220)
GREEN = (104, 220, 126)
YELLOW = (255, 211, 92)
PINK = (249, 106, 142)
ASSET_DIR = Path(__file__).resolve().parent / "assets"
AUDIO_DIR = ASSET_DIR / "audio"
CHARACTER_KEYS = (
    "player", "mario_type1", "mario_type2", "mario_type3", "mystery_player", "little_lizenian",
)
CHARACTER_PREVIEW_KEYS = (
    "player_preview",
    "mario_type1_preview",
    "mario_type2_preview",
    "mario_type3_preview",
    "mystery_player_preview",
    "little_lizenian_preview",
)
CHARACTER_NAMES = ("小精灵", "小马里奥", "中马里奥", "大马里奥", "神秘玩家", "小小李泽念")
CHARACTER_PREV_RECT = pygame.Rect(110, 278, 64, 64)
CHARACTER_NEXT_RECT = pygame.Rect(306, 278, 64, 64)
START_BUTTON_RECT = pygame.Rect(100, 380, 280, 60)


class Platform:
    """可踩踏的平台，位置使用世界坐标。"""

    def __init__(self, x: float, y: float, image: pygame.Surface):
        self.image = image
        self.rect = pygame.Rect(round(x), round(y), *image.get_size())

    def screen_rect(self, camera_y: float) -> pygame.Rect:
        """把世界坐标转换为屏幕坐标；镜头上移时，平台在屏幕上向下移动。"""
        return self.rect.move(0, round(camera_y))

    def draw(self, surface: pygame.Surface, camera_y: float) -> None:
        rect = self.screen_rect(camera_y)
        surface.blit(self.image, rect)


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
        self.assets = self._load_assets()
        pygame.display.set_caption("像素弹跳 - Pixel Jump")
        self.clock = pygame.time.Clock()
        self.font = self._font(22)
        self.small_font = self._font(16)
        self.title_font = self._font(42)
        self.character_index = 0
        self.clouds = [
            {"image": self.assets["cloud"], "x": -30.0, "y": 72, "speed": 0.45},
            {"image": self.assets["cloud_small"], "x": 310.0, "y": 42, "speed": -0.32},
            {"image": self.assets["cloud_small"], "x": 35.0, "y": 575, "speed": 0.26},
            {"image": self.assets["cloud"], "x": 400.0, "y": 625, "speed": -0.38},
        ]
        self.state = "menu"
        self.music_on = True
        self.sound_on = True
        self.best_score = self.load_record()
        audio_available = pygame.mixer.get_init() is not None
        self.bounce_sound = self._load_sound("small_jump.ogg") if audio_available else None
        self.pickup_sound = self._load_sound("金币音效.ogg") if audio_available else None
        self.death_sound = self._load_sound("死亡音效.wav") if audio_available else None
        self.load_track = AUDIO_DIR / "游戏前加载音效.ogg"
        self.game_track = AUDIO_DIR / "游戏音效.ogg"
        self.current_track = None
        self.reset()
        # reset() 用于开新局；首次启动仍应停留在主菜单。
        self.state = "menu"
        self.play_track(self.load_track)

    @staticmethod
    def _load_sound(filename: str) -> pygame.mixer.Sound:
        """从 assets/audio 加载短音效。"""
        return pygame.mixer.Sound(AUDIO_DIR / filename)

    def play_track(self, path: Path) -> None:
        """使用 Pygame 流式音乐播放器切换长音轨。"""
        if not pygame.mixer.get_init() or not self.music_on or not path.exists():
            return
        if self.current_track == path:
            return
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(loops=-1 if path == self.game_track else 0)
        self.current_track = path

    @staticmethod
    def _load_assets() -> dict[str, pygame.Surface]:
        """从 assets 目录加载所有游戏图片，不在运行时绘制图像素材。"""
        filenames = {
            "background": "background.png",
            "cloud": "cloud.png",
            "cloud_small": "cloud_small.png",
            "player": "player.png",
            "mario_type1": "mario_type1.png",
            "mario_type2": "mario_type2.png",
            "mario_type3": "mario_type3.png",
            "mystery_player": "mystery_player.png",
            "little_lizenian": "little_lizenian.png",
            "player_preview": "player_preview.png",
            "mario_type1_preview": "mario_type1_preview.png",
            "mario_type2_preview": "mario_type2_preview.png",
            "mario_type3_preview": "mario_type3_preview.png",
            "mystery_player_preview": "mystery_player_preview.png",
            "little_lizenian_preview": "little_lizenian_preview.png",
            "platform": "platform.png",
            "coin": "coin.png",
        }
        assets = {}
        for key, filename in filenames.items():
            image = pygame.image.load(ASSET_DIR / filename)
            assets[key] = image.convert() if key == "background" else image.convert_alpha()
        return assets

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
        self.start_y = self.player_y
        self.velocity_y = BOUNCE_SPEED
        self.camera_y = 0.0
        self.max_height = 0.0
        self.score_bonus = 0
        self.platforms = [Platform(WIDTH // 2 - 34, HEIGHT - 105, self.assets["platform"])]
        y = HEIGHT - 190
        while y > -300:
            self.platforms.append(Platform(random.randint(20, WIDTH - 88), y, self.assets["platform"]))
            y -= PLATFORM_GAP
        # 道具只增加分数，一局一个，便于初学者理解和实现。
        self.collectible = self.assets["coin"].get_rect(
            topleft=(random.randint(40, WIDTH - 56), HEIGHT - 350)
        )
        self.state = "playing"

    def cycle_character(self, direction: int) -> None:
        """在开始前循环选择可用角色。"""
        self.character_index = (self.character_index + direction) % len(CHARACTER_KEYS)

    @property
    def score(self) -> int:
        return int(self.max_height // 10) + self.score_bonus

    def play_sound(self, sound: pygame.mixer.Sound | None) -> None:
        if sound is not None and self.sound_on and pygame.mixer.get_init():
            sound.set_volume(0.7)
            sound.play()

    def update_music(self) -> None:
        if not pygame.mixer.get_init():
            return
        if not self.music_on:
            pygame.mixer.music.pause()
        else:
            pygame.mixer.music.unpause()
            if self.current_track is None:
                if self.state == "playing":
                    self.play_track(self.game_track)
                elif self.state == "menu":
                    self.play_track(self.load_track)

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
                screen_y = platform.screen_rect(self.camera_y).y
                if (previous_bottom <= screen_y + 3 and self.player.bottom >= screen_y
                        and self.player.right > platform.rect.left
                        and self.player.left < platform.rect.right):
                    self.player_y = float(screen_y - PLAYER_SIZE[1])
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

        # 世界坐标 = 屏幕坐标 - 镜头偏移；以开局位置为高度零点。
        current_height = self.start_y - self.player_y + self.camera_y
        self.max_height = max(self.max_height, current_height)

        # 持续在顶部补充普通平台，并回收离开画面的平台。
        self.platforms = [p for p in self.platforms if p.screen_rect(self.camera_y).y < HEIGHT + 40]
        while min((p.screen_rect(self.camera_y).y for p in self.platforms), default=HEIGHT) > -100:
            top_y = min((p.rect.y for p in self.platforms), default=self.camera_y) - PLATFORM_GAP
            self.platforms.append(Platform(random.randint(16, WIDTH - 84), top_y, self.assets["platform"]))

        if self.collectible:
            item_screen = self.collectible.move(0, round(self.camera_y))
            if self.player.colliderect(item_screen):
                self.collectible = None
                self.score_bonus += 100
                self.play_sound(self.pickup_sound)

        if self.player.top > HEIGHT:
            self.state = "over"
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                self.current_track = None
            self.play_sound(self.death_sound)
            if self.score > self.best_score:
                self.best_score = self.score
                self.save_record()

    def update_clouds(self) -> None:
        """让云层缓慢左右循环移动。"""
        for cloud in self.clouds:
            cloud["x"] += cloud["speed"]
            width = cloud["image"].get_width()
            if cloud["speed"] > 0 and cloud["x"] > WIDTH:
                cloud["x"] = -width
            elif cloud["speed"] < 0 and cloud["x"] + width < 0:
                cloud["x"] = WIDTH

    def draw_background(self) -> None:
        self.screen.blit(self.assets["background"], (0, 0))
        for cloud in self.clouds:
            self.screen.blit(cloud["image"], (round(cloud["x"]), cloud["y"]))

    def draw_player(self) -> None:
        """绘制已加载的小精灵图片。"""
        self.screen.blit(self.assets[CHARACTER_KEYS[self.character_index]], self.player)

    def draw_collectible(self) -> None:
        if not self.collectible:
            return
        item = self.collectible.move(0, round(self.camera_y))
        self.screen.blit(self.assets["coin"], item)

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
            self.text("像素弹跳", self.title_font, (WIDTH // 2, 145), YELLOW)
            self.text("踩住平台，向上跳得更高！", self.font, (WIDTH // 2, 205))
            self.text("选择角色", self.small_font, (WIDTH // 2, 260))
            self.text("‹", self.title_font, CHARACTER_PREV_RECT.center, WHITE)
            self.text("›", self.title_font, CHARACTER_NEXT_RECT.center, WHITE)
            character_image = self.assets[CHARACTER_PREVIEW_KEYS[self.character_index]]
            self.screen.blit(character_image, character_image.get_rect(center=(WIDTH // 2, 310)))
            self.text(CHARACTER_NAMES[self.character_index], self.font, (WIDTH // 2, 360), YELLOW)
            self.text("Enter 开始游戏", self.font, START_BUTTON_RECT.center, (35, 76, 120))
            self.text("← → 选择角色   M 音乐   N 音效", self.small_font, (WIDTH // 2, 475), (68, 105, 145))
            self.text("游戏中用 ← → 或 A / D 移动", self.small_font, (WIDTH // 2, 505), (68, 105, 145))
            self.text(f"历史最高分：{self.best_score}", self.small_font, (WIDTH // 2, 545), (68, 105, 145))
        else:
            self.text("游戏结束", self.title_font, (WIDTH // 2, 240), PINK)
            self.text(f"本局得分：{self.score}", self.font, (WIDTH // 2, 320))
            self.text(f"历史最高分：{self.best_score}", self.font, (WIDTH // 2, 365), YELLOW)
            self.text("按 Enter 或点击屏幕重新开始", self.font, (WIDTH // 2, 445), (35, 76, 120))
            self.text("按 Esc 返回主菜单", self.small_font, (WIDTH // 2, 490), WHITE)
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            self.clock.tick(FPS)
            self.update_clouds()
            self.update_music()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.music_on = not self.music_on
                    elif event.key == pygame.K_n:
                        self.sound_on = not self.sound_on
                    elif self.state == "menu" and event.key in (pygame.K_LEFT, pygame.K_a):
                        self.cycle_character(-1)
                    elif self.state == "menu" and event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.cycle_character(1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.state in ("menu", "over"):
                            self.reset()
                            self.play_track(self.game_track)
                    elif event.key == pygame.K_ESCAPE and self.state == "over":
                        self.state = "menu"
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.state == "menu":
                        if CHARACTER_PREV_RECT.collidepoint(event.pos):
                            self.cycle_character(-1)
                        elif CHARACTER_NEXT_RECT.collidepoint(event.pos):
                            self.cycle_character(1)
                        elif START_BUTTON_RECT.collidepoint(event.pos):
                            self.reset()
                            self.play_track(self.game_track)
                    elif self.state == "over":
                        self.reset()
                        self.play_track(self.game_track)
            self.update()
            self.draw()
        pygame.quit()


def main() -> None:
    """游戏入口。"""
    Game().run()


if __name__ == "__main__":
    main()
