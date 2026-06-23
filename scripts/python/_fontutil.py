"""
_fontutil.py — クロスプラットフォーム日本語フォント解決ヘルパ

Win/Mac/Linux のいずれでも、日本語が描画できるフォントを順次トライして返す。
全候補が失敗したら ImageFont.load_default() にフォールバック（警告のみ）。

使い方:
    from _fontutil import get_japanese_font
    font = get_japanese_font(size=40)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

try:
    from PIL import ImageFont
except ImportError:
    ImageFont = None  # type: ignore


# 候補リスト（OS横断・上から順にトライ）
FONT_CANDIDATES = [
    # Windows
    "C:/Windows/Fonts/YuGothB.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/yugothic.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/YuGothic-Bold.ttf",
    "C:/Windows/Fonts/YuGothic-Regular.ttf",
    # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Osaka.ttf",
    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    # 最後の砦（ASCIIのみ・日本語は描けない）
    "arial.ttf",
]


def get_japanese_font(size: int = 32, bold_preferred: bool = True):
    """
    日本語フォントを返す。見つからなければ load_default()（警告つき）。

    Args:
        size: フォントサイズ（pt）
        bold_preferred: True なら太字フォントを優先（候補リストの先頭から探索）

    Returns:
        PIL.ImageFont.FreeTypeFont または ImageFont.load_default()
    """
    if ImageFont is None:
        raise RuntimeError("Pillow が未インストールです。`pip install Pillow` を実行してください。")

    candidates = list(FONT_CANDIDATES)
    if not bold_preferred:
        # Bold/Regular の優先度を入れ替え（regular を先に）
        candidates.sort(key=lambda p: 0 if any(k in p.lower() for k in ["regular", "m.tt", "w3"]) else 1)

    for fp in candidates:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size=size)
            except Exception:
                continue
        # システムフォント検索（OS のフォントマップから名前で引く）
        try:
            return ImageFont.truetype(fp, size=size)
        except Exception:
            continue

    sys.stderr.write(
        "[_fontutil] 警告: 日本語フォントが見つかりませんでした。"
        "load_default() で続行します（日本語が文字化けする可能性）。\n"
    )
    return ImageFont.load_default()


def find_font_path() -> Optional[str]:
    """日本語フォントのパスを返す（見つからなければ None）。"""
    for fp in FONT_CANDIDATES:
        if Path(fp).exists():
            return fp
    return None


if __name__ == "__main__":
    p = find_font_path()
    if p:
        print(f"[OK] 日本語フォント検出: {p}")
        sys.exit(0)
    else:
        print("[WARN] 日本語フォントが見つかりません")
        sys.exit(1)
