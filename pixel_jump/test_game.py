"""核心游戏逻辑的回归测试，可用 python -m unittest 运行。"""

import os
import unittest
from unittest.mock import patch

# 使用 SDL 虚拟设备，不需要真实显示器或扬声器。
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from .game import Game, HEIGHT, Platform
import pygame


class GameLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        self.save_patch = patch.object(Game, "save_record", lambda _game: None)
        self.save_patch.start()
        self.game = Game()

    def tearDown(self) -> None:
        self.save_patch.stop()
        pygame.quit()

    def test_game_opens_on_menu(self) -> None:
        self.assertEqual(self.game.state, "menu")
        self.game.draw()

    def test_all_image_assets_load_and_clouds_move_both_ways(self) -> None:
        self.assertEqual(
            set(self.game.assets),
            {
                "background", "cloud", "cloud_small", "player", "player_preview",
                "mario_type1", "mario_type1_preview", "mario_type2", "mario_type2_preview",
                "mario_type3", "mario_type3_preview", "mystery_player", "mystery_player_preview",
                "platform", "coin",
            },
        )
        for key in ("player", "mario_type1", "mario_type2", "mario_type3", "mystery_player"):
            self.assertEqual(self.game.assets[key].get_size(), (28, 32))
            self.assertTrue(self.game.assets[key].get_flags() & pygame.SRCALPHA)
            self.assertEqual(self.game.assets[key].get_at((0, 0)).a, 0)
        for key in (
            "player_preview", "mario_type1_preview", "mario_type2_preview",
            "mario_type3_preview", "mystery_player_preview",
        ):
            self.assertEqual(self.game.assets[key].get_size(), (56, 64))
        self.assertEqual(self.game.assets["coin"].get_size(), (16, 16))
        start_positions = [cloud["x"] for cloud in self.game.clouds]

        self.game.update_clouds()

        self.assertGreater(self.game.clouds[0]["x"], start_positions[0])
        self.assertLess(self.game.clouds[1]["x"], start_positions[1])

    def test_all_five_characters_can_be_previewed_and_cycle(self) -> None:
        for expected_index in range(5):
            self.assertEqual(self.game.character_index, expected_index)
            self.game.draw()
            self.game.cycle_character(1)
        self.assertEqual(self.game.character_index, 0)

    def test_keyboard_selects_character_and_starts_game(self) -> None:
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        self.game.run()

        self.assertEqual(self.game.state, "playing")
        self.assertEqual(self.game.character_index, 1)
        self.game.reset()
        self.assertEqual(self.game.character_index, 1)

    def test_menu_arrow_click_selects_mario(self) -> None:
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(338, 310), button=1))
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        pygame.event.post(pygame.event.Event(pygame.QUIT))

        self.game.run()

        self.assertEqual(self.game.character_index, 1)
        self.assertEqual(self.game.state, "playing")

    def test_landing_from_above_triggers_one_bounce(self) -> None:
        self.game.state = "playing"
        platform = Platform(100, 300, self.game.assets["platform"])
        self.game.platforms = [platform]
        self.game.collectible = None
        self.game.player.x = 110
        self.game.player_y = 267.0
        self.game.player.y = 267
        self.game.velocity_y = 1.0

        self.game.update()

        self.assertEqual(self.game.velocity_y, -11.5)
        self.assertEqual(self.game.player.bottom, platform.screen_rect(self.game.camera_y).top)

    def test_landing_position_uses_scrolled_screen_coordinates(self) -> None:
        self.game.state = "playing"
        self.game.camera_y = 50
        platform = Platform(100, 300, self.game.assets["platform"])
        self.game.platforms = [platform]
        self.game.collectible = None
        self.game.player.x = 110
        self.game.player_y = 317.0
        self.game.player.y = 317
        self.game.velocity_y = 1.0

        self.game.update()

        self.assertEqual(self.game.velocity_y, -11.5)
        self.assertEqual(self.game.player.bottom, platform.screen_rect(self.game.camera_y).top)

    def test_rising_through_platform_does_not_bounce(self) -> None:
        self.game.state = "playing"
        self.game.platforms = [Platform(100, 300, self.game.assets["platform"])]
        self.game.collectible = None
        self.game.player.x = 110
        self.game.player_y = 310.0
        self.game.player.y = 310
        self.game.velocity_y = -4.0

        self.game.update()

        self.assertLess(self.game.velocity_y, 0)

    def test_camera_moves_platforms_down_and_height_increases(self) -> None:
        self.game.state = "playing"
        platform = Platform(100, 300, self.game.assets["platform"])
        self.game.platforms = [platform]
        self.game.collectible = None
        self.game.player_y = 260.0
        self.game.player.y = 260
        self.game.velocity_y = -1.0

        self.game.update()

        self.assertGreater(self.game.camera_y, 0)
        self.assertEqual(platform.screen_rect(self.game.camera_y).y, 300 + round(self.game.camera_y))
        self.assertGreater(self.game.max_height, 0)
        self.assertGreater(self.game.score, 0)

    def test_collectible_awards_100_points(self) -> None:
        self.game.state = "playing"
        self.game.platforms = []
        self.game.collectible = pygame.Rect(200, 300, 16, 16)
        self.game.player = self.game.collectible.copy()
        self.game.player_y = float(self.game.player.y)
        self.game.velocity_y = 0.0

        self.game.update()

        self.assertIsNone(self.game.collectible)
        self.assertEqual(self.game.score_bonus, 100)

    def test_fall_ends_round_and_reset_starts_new_round(self) -> None:
        self.game.state = "playing"
        self.game.platforms = []
        self.game.collectible = None
        self.game.player.y = HEIGHT + 1
        self.game.player_y = float(self.game.player.y)
        self.game.velocity_y = 1.0

        self.game.update()
        self.assertEqual(self.game.state, "over")

        self.game.reset()
        self.assertEqual(self.game.state, "playing")
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.camera_y, 0)


if __name__ == "__main__":
    unittest.main()
