"""
auto_convert_tables.py — article.md 内のマークダウン表を自動検出し、画像化＋本文置換する。

note.com はマークダウン表を描画しないため、本フェーズで全テーブルを画像に置換する。

使い方:
    python auto_convert_tables.py --input output/articles/{slug}/article.md
    python auto_convert_tables.py --input ... --punch "デフォルトのパンチライン"

動作:
    1. article.md を読み込み、`| ... | ... |` パターンの表を全検出
    2. 各表を images/figure_table_NN.png に PIL で描画
    3. 本文中の表記法を `![alt](images/figure_table_NN.png)` に置換
    4. 元の article.md を上書き保存（バックアップは article.md.bak）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# スクリプト自身のディレクトリ
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    from _fontutil import get_japanese_font
    from PIL import Image, ImageDraw
except ImportError as e:
    sys.stderr.write(f"[ERROR] 必要モジュールなし: {e}\n  pip install Pillow\n")
    sys.exit(1)

# HTML→PNG ルートが使えるか判定（Playwright がインストール済みかどうか）
def _html_route_available() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec("playwright") is not None
    except Exception:
        return False


HTML_TEMPLATE_PATH = HERE.parent / "templates" / "html" / "table_light.html"
HTML_TO_PNG_SCRIPT = HERE / "html_to_png.py"


# テーブル検出: 連続する `| ... |` 行（区切り行 |---|---| を含む）
TABLE_RE = re.compile(
    r"(?:^\|[^\n]+\|\s*\n)+",
    re.MULTILINE,
)


def parse_table(table_text: str):
    """マークダウンテーブル文字列を (headers, rows) に分解。"""
    lines = [l.strip() for l in table_text.strip().splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        return None

    def split_row(line: str):
        # 最初と最後の | を除去してから | で分割
        inner = line.strip().strip("|")
        return [c.strip() for c in inner.split("|")]

    headers = split_row(lines[0])
    # 区切り行（---）を判定
    sep_idx = -1
    for i, l in enumerate(lines[1:3], start=1):
        if all(c.strip().replace("-", "").replace(":", "") == "" for c in split_row(l)):
            sep_idx = i
            break

    if sep_idx == -1:
        # 区切り行がない場合は全行データとみなす
        rows = [split_row(l) for l in lines[1:]]
    else:
        rows = [split_row(l) for l in lines[sep_idx + 1:]]

    # 列数を揃える
    n_cols = len(headers)
    rows = [r[:n_cols] + [""] * (n_cols - len(r)) for r in rows]

    return headers, rows


def render_table_png(headers, rows, output_path: Path, title: str = "", punch: str = "重要ポイントを一目で"):
    """テーブルを PNG に描画。figure_template_table.py と同じロジック。"""
    W, H = 1280, 720
    BAND_H = int(H * 0.13)

    img = Image.new("RGB", (W, H), color=(248, 250, 253))
    draw = ImageDraw.Draw(img)

    # タイトル
    if title:
        title_font = get_japanese_font(size=52)
        tb = draw.textbbox((0, 0), title, font=title_font)
        draw.text(((W - (tb[2] - tb[0])) // 2, 25), title, font=title_font, fill=(30, 30, 30))
        table_top = 130
    else:
        table_top = 50

    table_h = H - BAND_H - table_top - 30
    n_cols = len(headers)
    n_rows = len(rows)

    margin = 40
    total_w = W - margin * 2
    col_w = total_w // n_cols if n_cols > 0 else total_w

    header_h = 80
    row_h = (table_h - header_h) // max(n_rows, 1)

    # フォント自動調整
    max_text_len = max(
        [len(s) for s in headers] +
        [len(c) for r in rows for c in r] +
        [1]
    )
    if max_text_len <= 6:
        cell_size = 38
    elif max_text_len <= 9:
        cell_size = 32
    elif max_text_len <= 12:
        cell_size = 28
    elif max_text_len <= 16:
        cell_size = 24
    else:
        cell_size = 20

    hf = get_japanese_font(size=max(cell_size + 4, 30))
    rf = get_japanese_font(size=cell_size)

    def draw_centered(txt, x, y, w, h, font, fill):
        max_chars_per_line = max(1, int(w / (cell_size * 0.7)))
        lines = []
        cur = ""
        for ch in txt:
            cur += ch
            if len(cur) >= max_chars_per_line:
                lines.append(cur); cur = ""
            if len(lines) >= 2:
                break
        if cur and len(lines) < 2:
            lines.append(cur)
        line_h = cell_size + 6
        total_h = line_h * len(lines)
        sy = y + (h - total_h) // 2
        for i, line in enumerate(lines):
            b = draw.textbbox((0, 0), line, font=font)
            sx = x + (w - (b[2] - b[0])) // 2
            draw.text((sx, sy + i * line_h), line, font=font, fill=fill)

    # ヘッダー
    for i, header in enumerate(headers):
        x0 = margin + i * col_w
        draw.rectangle([x0, table_top, x0 + col_w, table_top + header_h], fill=(52, 73, 94))
        draw_centered(header, x0, table_top, col_w, header_h, hf, (255, 255, 255))

    # 各行
    for r, row in enumerate(rows):
        y0 = table_top + header_h + r * row_h
        bg = (255, 255, 255) if r % 2 == 0 else (240, 245, 250)
        draw.rectangle([margin, y0, margin + col_w * n_cols, y0 + row_h], fill=bg)
        for c, cell in enumerate(row):
            x0 = margin + c * col_w
            text_color = (52, 152, 219) if c == 0 else (50, 50, 50)
            draw_centered(str(cell), x0, y0, col_w, row_h, rf, text_color)

    # 罫線
    for i in range(n_cols + 1):
        x = margin + i * col_w
        draw.line([(x, table_top), (x, table_top + header_h + row_h * n_rows)],
                  fill=(180, 180, 180), width=1)
    draw.line([(margin, table_top + header_h),
               (margin + col_w * n_cols, table_top + header_h)],
              fill=(180, 180, 180), width=2)

    # パンチライン帯
    draw.rectangle([0, H - BAND_H, W, H], fill=(255, 215, 0))
    pf = get_japanese_font(size=52)
    pb = draw.textbbox((0, 0), punch, font=pf)
    draw.text(((W - (pb[2] - pb[0])) // 2,
               H - BAND_H + (BAND_H - (pb[3] - pb[1])) // 2),
              punch, font=pf, fill=(0, 0, 0))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


def find_preceding_heading(md: str, table_start: int) -> str:
    """表の直前にある見出し（H2/H3）を返す。見つからなければ空文字。"""
    head = md[:table_start]
    matches = list(re.finditer(r"^(#{2,3})\s+(.+)$", head, re.MULTILINE))
    if matches:
        return matches[-1].group(2).strip()
    return ""


def render_table_via_html(headers, rows, output_path: Path, title: str) -> bool:
    """Playwright + table_light.html で高品質画像を生成。失敗したら False を返す。"""
    if not HTML_TEMPLATE_PATH.exists() or not HTML_TO_PNG_SCRIPT.exists():
        return False

    import json
    import subprocess
    import tempfile

    html = HTML_TEMPLATE_PATH.read_text(encoding="utf-8")

    # tbody の中身を差し替え
    thead_cells = "".join(f"<th>{h}</th>" for h in headers)
    tbody_rows = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
        for r in rows
    )

    # 既存テンプレ内のダミーデータを置換
    new_thead = f"<thead><tr>{thead_cells}</tr></thead>"
    new_tbody = f"<tbody>{tbody_rows}</tbody>"
    html = re.sub(r"<thead>.*?</thead>", new_thead, html, count=1, flags=re.DOTALL)
    html = re.sub(r"<tbody>.*?</tbody>", new_tbody, html, count=1, flags=re.DOTALL)
    # タイトル差し替え
    html = re.sub(
        r'(<div class="head"[^>]*>)[^<]*(</div>)',
        rf'\g<1>{title}\g<2>',
        html, count=1,
    )

    # 一時 HTML を テンプレと同じディレクトリに置く（_base.css への相対参照を維持）
    tmp_html = HTML_TEMPLATE_PATH.parent / f"_gen_table_{output_path.stem}.html"
    try:
        tmp_html.write_text(html, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(HTML_TO_PNG_SCRIPT),
             "--html", str(tmp_html),
             "--output", str(output_path),
             "--width", "1280", "--height", "720", "--scale", "2"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.stderr.write(f"[WARN] HTML→PNG 失敗、PILにフォールバック: {result.stderr}\n")
            return False
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        sys.stderr.write(f"[WARN] HTML経路で例外、PILにフォールバック: {e}\n")
        return False
    finally:
        if tmp_html.exists():
            try:
                tmp_html.unlink()
            except Exception:
                pass


def convert(input_md: Path, default_punch: str = "重要ポイントを一目で") -> int:
    md = input_md.read_text(encoding="utf-8")
    images_dir = input_md.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    use_html = _html_route_available()
    if use_html:
        print("[INFO] Playwright を検出 → 高品質HTML経路を使用")
    else:
        print("[INFO] Playwright なし → PIL経路を使用（pip install -r requirements-html.txt で高品質化可能）")

    converted = 0

    def repl(match: re.Match):
        nonlocal converted
        table_text = match.group(0)
        parsed = parse_table(table_text)
        if not parsed:
            return table_text
        headers, rows = parsed
        if len(headers) < 2 or len(rows) < 1:
            return table_text

        converted += 1
        png_name = f"figure_table_{converted:02d}.png"
        png_path = images_dir / png_name
        title = find_preceding_heading(md, match.start()) or "比較表"

        rendered = False
        if use_html:
            rendered = render_table_via_html(headers, rows, png_path, title=title)
        if not rendered:
            render_table_png(headers, rows, png_path, title=title, punch=default_punch)

        rel = f"images/{png_name}"
        alt = title
        route = "HTML" if (use_html and rendered) else "PIL"
        print(f"[OK] table#{converted} ({route}) → {png_path}")
        return f"\n![{alt}]({rel})\n"

    new_md = TABLE_RE.sub(repl, md)

    if converted > 0:
        # バックアップ
        bak = input_md.with_suffix(input_md.suffix + ".bak")
        bak.write_text(md, encoding="utf-8")
        input_md.write_text(new_md, encoding="utf-8")
        print(f"[OK] {converted} 個のテーブルを画像化し、本文を更新（バックアップ: {bak.name}）")
    else:
        print("[INFO] マークダウン表は検出されませんでした")

    return converted


def main() -> int:
    ap = argparse.ArgumentParser(description="article.md の表を自動的に画像化")
    ap.add_argument("--input", required=True, help="入力 article.md")
    ap.add_argument("--punch", default="重要ポイントを一目で", help="表のパンチライン帯テキスト")
    args = ap.parse_args()

    p = Path(args.input)
    if not p.exists():
        sys.stderr.write(f"[ERROR] ファイルなし: {p}\n")
        return 1

    convert(p, default_punch=args.punch)
    return 0


if __name__ == "__main__":
    sys.exit(main())
