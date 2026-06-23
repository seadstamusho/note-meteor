# note-meteor

テーマを渡すだけで、記事執筆・サムネ生成・note.com下書き投稿まで全自動で完結するClaude Codeスキルです。

- APIキー不要（note.comのログインセッションのみ使用）
- 差し込み画像はHTML自動生成 or Codex CLI生成の2択
- 下書き保存後、ハッシュタグをターミナルに出力（コピペで設定）

## 必要なもの

- [Claude Code](https://claude.ai/code)（インストール済みであること）
- Node.js 18以上
- Python 3.9以上
- note.comアカウント

## セットアップ（初回のみ）

Claude Codeのチャット欄でスキルを起動すると、自動でセットアップが走ります。

唯一の手動ステップはnote.comへのログインです。スキルの案内に従い、チャット欄に以下を入力してEnterを押してください：

```
! npm run login
```

ブラウザが開くので、note.comにいつも通りログインして閉じてください。次回からは不要です。

## 使い方

Claude Codeのチャット欄に以下のように入力：

```
note-meteorスキルを使って「〇〇について」という記事を書いて
```

スキルがテーマをもとにリサーチ → 執筆 → 画像生成 → 下書き投稿まで進めます。

## ファイル構成

```
note-meteor/
├── scripts/
│   ├── node/
│   │   ├── login-note.js        # 初回ログイン用
│   │   └── publish-hybrid.js    # note.com投稿
│   └── python/
│       ├── html_to_png.py       # 画像生成
│       └── auto_convert_tables.py
├── templates/html/              # 画像テンプレート
├── .claude/skills/note-auto/    # スキル定義
├── .env.example                 # 設定ファイルのサンプル
└── requirements.txt
```

## 注意

- `.note-state.json`（ログインセッション）はGitに含まれません。各自でログインが必要です。
- `.env`もGitに含まれません。必要な場合は`.env.example`を参考に作成してください。
