# 像素弹跳

一个面向 Python 初学者的 Pygame 自动弹跳平台小游戏。游戏图片和音频素材都保存在项目目录中。

游戏图片保存在 `assets/` 中，运行时从 PNG 文件加载；云层会在蓝天背景上缓慢左右循环移动。开始前可用左右键或菜单箭头在小精灵、三种马里奥、神秘玩家和小小李泽念之间切换。`process_character_assets.py` 用于重新处理金币、马里奥图集及角色源图；它需要 Pillow。

加载音轨、游戏音轨、跳跃、金币和死亡音效保存在 `assets/audio/` 中并从此目录加载。菜单加载音轨播放一次；开始游戏后切换为循环游戏音轨。

## 运行

```powershell
python -m pip install pygame
python -m pixel_jump
```

请在项目根目录运行第二条命令。

## 测试

```powershell
python -m unittest pixel_jump.test_game
```

## 操作

- `←` / `→` 或 `A` / `D`：左右移动
- `Enter` 或 `Space`：开始或重新开始
- `M`：切换背景音乐
- `N`：切换音效
- 游戏结束画面按 `Esc`：返回主菜单

踩中平台会自动弹跳；到达更高高度会增加分数，碰到金色道具获得 100 分。掉出屏幕底部后本局结束，历史最高分保存在用户目录。
