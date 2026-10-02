"""封装游戏音效与背景音乐的加载、播放和开关控制。"""

from pathlib import Path

import pygame

from config import AUDIO_DIR


class AudioManager:
    """在初始化时加载短音效，并管理两首流式背景音轨。"""

    def __init__(self, audio_dir: Path = AUDIO_DIR) -> None:
        self.audio_dir = audio_dir
        self.enabled = pygame.mixer.get_init() is not None
        self.music_enabled = True
        self.sound_enabled = True
        self._music_paused = False
        self.current_track: Path | None = None
        self.load_track = audio_dir / "游戏前加载音效.ogg"
        self.game_track = audio_dir / "游戏音效.ogg"

        self.bounce_sound = self._load_sound("small_jump.ogg")
        self.pickup_sound = self._load_sound("金币音效.ogg")
        self.death_sound = self._load_sound("死亡音效.wav")

    def _load_sound(self, filename: str) -> pygame.mixer.Sound | None:
        """音频设备不可用时返回 None，让游戏仍可静音运行。"""
        if not self.enabled:
            return None
        return pygame.mixer.Sound(self.audio_dir / filename)

    def play_sound(self, sound: pygame.mixer.Sound | None) -> None:
        """播放已加载的短音效，不在触发时重新读取文件。"""
        if self.enabled and self.sound_enabled and sound is not None:
            sound.set_volume(0.7)
            sound.play()

    def play_track(self, path: Path, loop: bool = False) -> None:
        """切换流式背景音轨；音乐资源不会被解码成多份常驻对象。"""
        if not self.enabled or not self.music_enabled or not path.is_file():
            return
        if self.current_track == path:
            return
        pygame.mixer.music.load(str(path))
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(loops=-1 if loop else 0)
        self.current_track = path

    def stop_track(self) -> None:
        """停止当前背景音乐并清空正在播放的音轨标记。"""
        if self.enabled:
            pygame.mixer.music.stop()
        self.current_track = None
        self._music_paused = False

    def update(self, game_state: str) -> None:
        """应用静音状态，并在音乐结束后按游戏状态恢复合适音轨。"""
        if not self.enabled:
            return
        if not self.music_enabled:
            if not self._music_paused:
                pygame.mixer.music.pause()
                self._music_paused = True
            return

        if self._music_paused:
            pygame.mixer.music.unpause()
            self._music_paused = False
        if self.current_track is None:
            if game_state == "playing":
                self.play_track(self.game_track, loop=True)
            elif game_state == "menu":
                self.play_track(self.load_track)
