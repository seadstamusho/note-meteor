---
name: note-meteor
description: >
  テーマを渡すだけで、記事執筆・サムネ＆図解生成・ハッシュタグ設定・
  note.com下書き投稿まで全自動で完結するスキル。
  差し込み画像はHTML自動生成 or Codex CLIの2択。
---

# note-auto — note全自動投稿スキル

**このスキルの責任範囲**：テーマ入力 → 記事生成 → 画像生成 → note.com下書き投稿

---

## Phase 0. セットアップ（ほぼ自動・ユーザー操作は最小限）

`.note-setup-done` が存在するか確認する（私が実行）：

```bash
node -e "import {existsSync} from 'fs'; console.log(existsSync('.note-setup-done')?'SKIP':'SETUP');" --input-type=module
```

### `SKIP` → Phase 1 へ即進む（以下すべてスキップ）

### `SETUP` → 私（Claude Code）が以下を自動実行する

**0-1. Node.js依存パッケージ（私が自動実行）**

```bash
npm install
npx playwright install chromium
```

**0-2. Pythonパッケージ（私が自動実行）**

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

**0-3. note.comセッション確認（私が自動実行）**

```bash
node -e "import {existsSync} from 'fs'; import {homedir} from 'os'; import {join} from 'path'; const p=join(homedir(),'.note-state.json'); console.log(existsSync(p)?'SESSION_OK':'SESSION_MISSING');" --input-type=module
```

`SESSION_MISSING` の場合のみ、以下をユーザーに表示してEnterを待つ：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔑 note.comへのログインが必要です（初回のみ・1分で完了）

この画面（チャット欄）に以下をそのままコピペしてEnterを押してください：

   ! npm run login

ブラウザが自動で開くので、note.comにいつも通りログインして閉じてください。
閉じたら「できた」と教えてください。次回からはこの手順は不要です。

※ ターミナルを別で開いている方は「!」なしで npm run login を実行してもOKです。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**0-4. セットアップ完了マーク（私が自動実行）**

```bash
node -e "import {writeFileSync} from 'fs'; writeFileSync('.note-setup-done','');" --input-type=module
```

> 再セットアップが必要な場合：チャット欄に `! del .note-setup-done` と入力 → スキル再起動

**このスキルはAPIキー不要です。**
note.comのログインセッション（ブラウザCookie）だけで動作します。

全チェックOKなら → Phase 1 へ進む。

---

## Phase 1. 入力整理（最初に1回・必須質問）

### 1-1. 記事スタイルを確認

```
記事のスタイルを教えてください：

  [1] 有料記事向け（購買意欲を高める感情訴求型）
      → 数値・限定性・恐怖→希望サイクルを使った販売に強い文体

  [2] 無料記事・読み物（有益情報をわかりやすく届けるスタイル）
      → 体験談・共感ベース、カジュアル丁寧体

  [3] その他（自由入力）

どれにしますか？迷ったら [2] がおすすめです。
```

### 1-2. 文字数を確認

```
記事の文字数はどのくらいにしますか？

  [1] 3,000文字（短め・スマホでサクッと読み切れる）
  [2] 10,000文字（長文・SEOと網羅性重視）
  [3] 自由入力（数値で指定）

迷ったら [1] からスタートがおすすめです。
```

### 1-3. 差し込み画像の生成方法を確認（★重要・丁寧に説明する）

```
記事内に入れる差し込み画像（サムネ・図解）の生成方法を選んでください。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [A] Claude Codeにおまかせ（推奨）
      → HTML＋Playwrightで自動生成。
        シンプルなデザインですが、私（Claude Code）が
        全部やるので追加作業ゼロです。
        Codex CLIがなくても動きます。

  [B] Codex CLIで本格生成（手動ステップあり）
      → ChatGPT ProプランのCodex CLIを使ってAI画像生成。
        本格的なビジュアルが作れますが、
        生成プロンプトを私が書いた後、
        しょうくん自身がCodexに貼り付ける作業が必要です。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

「おまかせ」「どちらでもいい」「Codex CLIは持っていない」
→ 自動的に [A] を選びます。

どちらにしますか？
```

**回答マッピング：**
- 「A」「おまかせ」「自動」「持っていない」「わからない」「どちらでも」→ `image_mode = "playwright"`
- 「B」「Codex」「本格」「手動でもいい」→ `image_mode = "codex"`

その他の不足項目は仮置きで走り出す。

---

## Phase 2. リサーチ（必須・憶測禁止）

WebSearch + WebFetch で以下を収集：
- 主要事実・数値（出典URL付き必須）
- 具体例・ケーススタディ 3つ以上
- 反対意見・注意点 1つ以上
- 関連キーワード・ハッシュタグ候補

`output/{YYYYMMDD}_{slug}/research.md` に保存。

**品質ゲート（合格まで進めない）：**
- 出典URL 3個以上
- 数値・固有名詞 5個以上
- 不足ならリサーチ追加（最大3回）

---

## Phase 3. 記事フォルダ作成

```
output/{YYYYMMDD}_{slug}/
├── images/
└── metadata.json
```

`metadata.json` の初期値：
```json
{
  "title": "",
  "slug": "",
  "created_at": "YYYY-MM-DDTHH:MM:SS",
  "tags": [],
  "target_reader": "",
  "tone": "",
  "article_style": "sales | info | custom",
  "style_notes": "",
  "target_chars": 3000,
  "actual_chars": 0,
  "image_mode": "playwright | codex",
  "research_path": "research.md",
  "notes": ""
}
```

---

## Phase 4. 本文 Markdown 作成

### 4-0. スタイルガイド読み込み（必須）

執筆開始前に `.claude/skills/note-auto/references/style-guide.md` を Read し、
`article_style` に応じたセクション（A/B/C）を唯一の根拠として使う。

### 4-1. 記事構造テンプレート

`output/{YYYYMMDD}_{slug}/article.md` に出力：

```markdown
---
title: "記事タイトル"
tags: ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"]
---

（冒頭フック：個人体験・共感から始める。1〜2段落）

![サムネイル](images/thumbnail.png)

## 大見出し1

### 小見出し1-1

本文…

![図解1：〇〇のイメージ](images/figure_01.png)

### 小見出し1-2

本文…

## 大見出し2

### 小見出し2-1

本文…

![図解2：△△の流れ](images/figure_02.png)

## まとめ

（要点を3〜5個の箇条書き + 次のアクション）
```

### 4-2. note.com 互換ルール（厳守）

| 記法 | note挙動 | 対応 |
|------|---------|------|
| テーブル `\| col \|` | パイプがそのまま表示 | **禁止 → 図解画像に変換** |
| HTML タグ | 無視またはエスケープ | 禁止 |
| 脚注 `[^1]` | 反映されない | 本文に直接書く |

**必ず守ること：**
- H2大見出し 3〜5個
- 各H2にH3小見出し 2個以上
- 図解プレースホルダを本文中に最低2枚
- 文末に「## まとめ」セクション
- 箇条書き・引用ブロック（`> `）・**太字** を適切に使用

---

## Phase 5. 画像生成

### image_mode = "playwright" の場合（A選択）

#### 5-A-1. Playwright 存在チェック

```bash
python -c "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('playwright') else 1)"
```

#### 5-A-2. 未インストールなら自動セットアップ（質問しない）

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

#### 5-A-3. 生成対象（必須3枚・質問しない）

| ファイル | テンプレ | 用途 |
|---------|---------|------|
| `images/thumbnail.png` | `templates/html/thumbnail_light.html` | サムネイル |
| `images/figure_01.png` | `templates/html/steps_roadmap_light.html` | ステップ・フロー図 |
| `images/figure_02.png` | `templates/html/compare_card_light.html` | 比較・Before/After |

**実行手順（各画像について）：**

```bash
# 1. テンプレをtemplates/html/内でコピー（_base.cssと同じディレクトリが必要）
cp "templates/html/thumbnail_light.html" "templates/html/_gen_thumbnail.html"

# 2. Edit ツールで _gen_thumbnail.html の内容を記事に合わせて書き換え
#    （figure-patterns.md の文字数制限・禁止事項を必ず読む）

# 3. PNG化
python scripts/python/html_to_png.py \
  --html "templates/html/_gen_thumbnail.html" \
  --output "output/{YYYYMMDD}_{slug}/images/thumbnail.png" \
  --width 1280 --height 720 --scale 2

# 4. 確認・後始末
rm "templates/html/_gen_thumbnail.html"
```

3枚（thumbnail / figure_01 / figure_02）について繰り返す。

#### 5-A-4. B2フォールバック（Playwright失敗時のみ）

PILテンプレート（`scripts/python/figure_template_*.py`）で代替生成。

---

### image_mode = "codex" の場合（B選択）

#### 5-B-1. 差し込みプロンプトを生成して提示

各画像について Codex CLI用のプロンプトを作成し、以下の形式で出力する：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Codex CLI 用プロンプト — サムネイル
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
下記をそのまま Codex CLI に貼り付けてください。

---
[記事テーマ]のnote記事用サムネイル画像を生成してください。
サイズ: 1280×720px
スタイル: [テーマに合った指示]
テキスト: "[記事タイトル]"
出力先: output/{YYYYMMDD}_{slug}/images/thumbnail.png
---

✅ 生成できたら「できた」と教えてください。次の図解プロンプトを出します。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### 5-B-2. ユーザー完了確認後、次の画像プロンプトへ

サムネ → figure_01 → figure_02 の順に1枚ずつ確認して進む。
全枚数のプロンプトを一気に出さない。

#### 5-B-3. 画像が揃ったら Phase 6 へ

---

## Phase 5.5. テーブル自動変換（全モード共通・必須）

```bash
python scripts/python/auto_convert_tables.py \
  --input "output/{YYYYMMDD}_{slug}/article.md" \
  --punch "重要ポイントを一目で"
```

```bash
grep -n "^|.*|" "output/{YYYYMMDD}_{slug}/article.md" || echo "[OK] 表記法残存なし"
```

---

## Phase 6. 品質チェック

### 6-1. 文字数チェック

```bash
python scripts/python/count_chars.py \
  --input "output/{YYYYMMDD}_{slug}/article.md" \
  --metadata "output/{YYYYMMDD}_{slug}/metadata.json"
```

| 判定 | アクション |
|------|----------|
| 範囲内（±10%） | OK |
| 不足 | リサーチから具体例を追記 |
| 超過 | 冗長部分を整理 |

最大3回まで再試行。

### 6-2. 画像生成確認ゲート（突破必須）

```bash
python -c "
import sys, pathlib
slug_dir = pathlib.Path('output/{YYYYMMDD}_{slug}')
required = ['images/thumbnail.png', 'images/figure_01.png', 'images/figure_02.png']
missing = [p for p in required if not (slug_dir / p).exists() or (slug_dir / p).stat().st_size < 5000]
if missing:
    print('MISSING=' + ','.join(missing)); sys.exit(1)
else:
    print('IMAGES_OK')
"
```

- `IMAGES_OK` → Phase 7 へ
- 不足 → Phase 5 を最大3周リトライ

---

## Phase 7. note.com 下書き投稿

### 7-1. セッション確認

```bash
node -e "
import { existsSync } from 'fs';
import { resolve, join } from 'path';
import { homedir } from 'os';
const p = process.env.NOTE_POST_MCP_STATE_PATH || join(homedir(), '.note-state.json');
console.log(existsSync(p) ? 'SESSION_OK' : 'SESSION_MISSING');
" --input-type=module
```

- `SESSION_MISSING` の場合：
  ```
  ⚠️ note.comのログインセッションがありません。
  先に以下を実行してログインしてください：

  node scripts/node/login-note.js

  ブラウザが開くので、note.comにログインして閉じてください。
  完了したら「できた」と教えてください。
  ```
  ユーザーの「できた」を待ってから次へ。

### 7-2. 投稿実行

```bash
node scripts/node/publish-hybrid.js \
  "output/{YYYYMMDD}_{slug}/article.md" \
  "output/{YYYYMMDD}_{slug}/images/thumbnail.png" \
  "draft" \
  "output/{YYYYMMDD}_{slug}/images"
```

ブラウザが自動で開き、note.comに下書き保存される。

---

## Phase 8. 完成報告

以下をまとめて提示：

1. **生成ファイル一覧**
   - `output/{YYYYMMDD}_{slug}/article.md` — 本文
   - `output/{YYYYMMDD}_{slug}/images/` — 画像（生成方式を明記）
   - `output/{YYYYMMDD}_{slug}/research.md` — リサーチ結果
2. **記事情報**
   - タイトル・タグ・文字数判定
3. **投稿結果**
   - note.comの下書きURL（ブラウザのURLバーを確認）
4. **次のアクション候補**
   - 画像の微調整（Codexモードの場合）
   - タグの追記・調整
   - 本文の人間レビュー

---

## 絶対にやらないこと

- マークダウン表（`| ... |`）を本文に残す
- `image_mode = "playwright"` なのに「画像どうしますか？」と再確認する
- `image_mode = "codex"` のプロンプトを全部一気に出す（1枚ずつ確認する）
- 図解・サムネなしで完成報告する（Phase 6-2 のゲートを必ず通す）
- セッションなしで投稿を試みる（SESSION_MISSING ならログインを先に案内する）
