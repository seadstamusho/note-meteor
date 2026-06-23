"""
count_chars.py — Markdown記事の本文文字数を厳密にカウントする。

frontmatter / 画像参照 / コードブロック / 引用記号 / 空白 を除外した「実本文」の文字数を返す。
metadata.json があれば actual_chars を更新し、target_chars との差分判定（±10%）も出力する。

使い方:
    python count_chars.py --input output/articles/20260423_x/article.md
    python count_chars.py --input ... --metadata output/articles/20260423_x/metadata.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
CODEBLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`]+`")
HEADING_MARK_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
QUOTE_MARK_RE = re.compile(r"^>\s+", re.MULTILINE)
LIST_MARK_RE = re.compile(r"^[-*+]\s+", re.MULTILINE)
HR_RE = re.compile(r"^---+\s*$", re.MULTILINE)
URL_RE = re.compile(r"https?://\S+")
WHITESPACE_RE = re.compile(r"\s+")


def count_body_chars(md: str) -> int:
    """frontmatter等を除いた本文の実文字数を返す。"""
    # frontmatter 除去（先頭にある場合のみ）
    body = FRONTMATTER_RE.sub("", md, count=1) if FRONTMATTER_RE.match(md) else md

    # コードブロック除去
    body = CODEBLOCK_RE.sub("", body)
    # 画像参照除去
    body = IMAGE_RE.sub("", body)
    # インラインコード除去
    body = INLINE_CODE_RE.sub("", body)
    # URL除去（裸URL）
    body = URL_RE.sub("", body)
    # 水平線・各種マーカー除去
    body = HR_RE.sub("", body)
    body = HEADING_MARK_RE.sub("", body)
    body = QUOTE_MARK_RE.sub("", body)
    body = LIST_MARK_RE.sub("", body)
    # 残りの空白を全削除
    body = WHITESPACE_RE.sub("", body)

    return len(body)


def judge(actual: int, target: int, tolerance: float = 0.10) -> str:
    """target ±tolerance 内なら OK、不足なら SHORT、超過なら OVER を返す。"""
    if target <= 0:
        return "UNKNOWN"
    lower = int(target * (1 - tolerance))
    upper = int(target * (1 + tolerance))
    if actual < lower:
        return "SHORT"
    if actual > upper:
        return "OVER"
    return "OK"


def main() -> int:
    ap = argparse.ArgumentParser(description="記事の本文文字数カウント・目標値判定")
    ap.add_argument("--input", required=True, help="入力 Markdown ファイル")
    ap.add_argument("--metadata", help="metadata.json（あれば actual_chars を更新・target_chars で判定）")
    ap.add_argument("--target", type=int, help="目標文字数（--metadata 不使用時）")
    ap.add_argument("--tolerance", type=float, default=0.10, help="許容誤差（既定 0.10 = ±10%）")
    args = ap.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        sys.stderr.write(f"[ERROR] 入力ファイルなし: {md_path}\n")
        return 1

    md = md_path.read_text(encoding="utf-8")
    actual = count_body_chars(md)
    print(f"actual_chars={actual}")

    target = args.target
    if args.metadata:
        meta_path = Path(args.metadata)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}
            meta["actual_chars"] = actual
            target = target or meta.get("target_chars")
            meta_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"[OK] metadata.json を更新: {meta_path}")

    if target:
        verdict = judge(actual, target, args.tolerance)
        lower = int(target * (1 - args.tolerance))
        upper = int(target * (1 + args.tolerance))
        print(f"target_chars={target}  range=[{lower}, {upper}]  verdict={verdict}")
        if verdict == "SHORT":
            print(f"[ACTION] 不足 {target - actual} 文字。リサーチ結果から追記してください。")
        elif verdict == "OVER":
            print(f"[ACTION] 超過 {actual - target} 文字。冗長部分を整理してください。")
        else:
            print("[ACTION] 文量OK。次フェーズへ進めます。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
