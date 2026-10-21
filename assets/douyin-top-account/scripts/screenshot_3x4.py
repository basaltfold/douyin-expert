#!/usr/bin/env python3
"""Chrome headless 3:4 截图脚本 — 自动测量高度并裁剪"""
import subprocess, json, sys, os
from pathlib import Path

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = Path(__file__).parent.parent / "output"
TARGET_W = 1080
TARGET_RATIO = 4 / 3  # height/width = 4:3 → 3:4 横竖
TARGET_H = int(TARGET_W * TARGET_RATIO)  # 1440


def measure_height(html_file: str) -> int:
    """用 Chrome DevTools Protocol 测量页面实际高度"""
    js = "document.documentElement.scrollHeight"
    # 使用 Chrome 的 --dump-dom + 内嵌 JS 不现实，改用直接设 viewport 截图后裁剪
    return 0  # fallback


def take_screenshot(html_file: str, out_png: str):
    """截图为 1080 宽，然后裁剪为 1440 高"""
    tmp = out_png + ".tmp.png"
    # 先用 1080 宽截图（高度自适应）
    subprocess.run([
        CHROME, "--headless", "--disable-gpu",
        f"--screenshot={tmp}",
        f"--window-size={TARGET_W},3000",
        "--force-device-scale-factor=2",
        "--hide-scrollbars",
        html_file
    ], capture_output=True, timeout=30)

    # 检查文件
    if not os.path.exists(tmp):
        print(f"[FAIL] 截图失败: {html_file}")
        return

    # 尝试用 Pillow 裁剪为 3:4
    try:
        from PIL import Image
        img = Image.open(tmp)
        w, h = img.size
        # 目标: 从顶部裁剪到 3:4
        target_h_px = int(w * TARGET_RATIO)
        if h < target_h_px:
            # 内容不够高，需要扩展画布（加底部深色背景）
            new_img = Image.new('RGB', (w, target_h_px), (10, 14, 43))  # 深蓝底色
            new_img.paste(img, (0, 0))
            new_img.save(out_png)
        else:
            cropped = img.crop((0, 0, w, target_h_px))
            cropped.save(out_png)
        os.remove(tmp)
        print(f"[OK] {out_png} ({img.size[0]}x{min(h, target_h_px)} → 3:4)")
    except ImportError:
        # 没有 Pillow，直接用 ffmpeg 或 ImageMagick 裁剪
        # 回退：直接用原始截图
        os.replace(tmp, out_png)
        print(f"[OK-PIL-MISS] {out_png} (未裁剪，请安装 Pillow)")


def main():
    pairs = [
        ("douyin_weekly_hot_accounts.html", "douyin_weekly_hot_accounts.png"),
        ("douyin_weekly_likes_surge.html", "douyin_weekly_likes_surge.png"),
    ]
    for html_name, png_name in pairs:
        html_path = OUTPUT_DIR / html_name
        png_path = OUTPUT_DIR / png_name
        if html_path.exists():
            take_screenshot(str(html_path), str(png_path))
        else:
            print(f"[SKIP] {html_name} 不存在")


if __name__ == "__main__":
    main()
