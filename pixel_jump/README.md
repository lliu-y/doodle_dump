# 像素弹跳

一个面向 Python 初学者的 Pygame 自动弹跳平台小游戏。所有图形和声音都由程序生成，不需要下载素材。

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
