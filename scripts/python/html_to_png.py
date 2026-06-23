"""
html_to_png.py — HTMLテンプレを Playwright で 1280x720 PNG に変換する。

Playwright が未インストールの場合は明確にエラー終了し、PILテンプレへの
フォールバック方法を案内する。

使い方:
    python html_to_png.py --html templates/html/thumbnail_light.html \
                           --output output/articles/{slug}/images/thumbnail.png
    python html_to_png.py --html ./_gen_table.html \
                           --output ./images/figure_table_01.png \
                           --width 1280 --height 720

オプション:
    --width / --height   ビューポートサイズ（既定 1280x720）
    --scale              deviceScaleFactor（既定 2、Retina相当）
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def convert(html_path: Path, output_path: Path, width: int = 1280, height: int = 720, scale: int = 2) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.stderr.write(
            "[ERROR] Playwright が未インストールです。\n"
            "  高品質HTML経路を使うには以下を実行：\n"
            "    pip install -r requirements-html.txt\n"
            "    playwright install chromium\n"
            "  または、PILテンプレ（figure_template_*.py）にフォールバックしてください。\n"
        )
        return False

    if not html_path.exists():
        sys.stderr.write(f"[ERROR] HTML が見つかりません: {html_path}\n")
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    file_url = html_path.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
        )
        page = context.new_page()
        page.goto(file_url, wait_until="networkidle")
        # Webフォント描画完了を待つ
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(output_path), full_page=False, omit_background=False)
        browser.close()

    size_kb = output_path.stat().st_size // 1024
    print(f"[OK] {output_path} ({width}x{height} @{scale}x, {size_kb} KB)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="HTML → PNG 変換（Playwright）")
    ap.add_argument("--html", required=True, help="入力 HTML ファイル")
    ap.add_argument("--output", required=True, help="出力 PNG パス")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    ok = convert(Path(args.html), Path(args.output), args.width, args.height, args.scale)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
