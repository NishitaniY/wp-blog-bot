# wp-blog-bot

`drafts/` にマークダウン記事を置くと、GitHub Actions が自動で WordPress に下書き投稿するパイプライン。

## セットアップ

### 1. GitHub Secrets に登録

| Secret名 | 説明 |
|---|---|
| `WP_URL` | WordPressサイトURL（例: `https://example.com`） |
| `WP_USER` | WP管理者ユーザー名 |
| `WP_APP_PASSWORD` | WPアプリケーションパスワード |

### 2. WPアプリケーションパスワードの発行

WP管理画面 → ユーザー → プロフィール → アプリケーションパスワード から発行。

### 3. 記事を投稿する

1. `drafts/` にマークダウンファイルを置いて push
2. Actions → WP Auto Post → Run workflow（手動実行）
3. または毎週月曜 7:00 JST に自動実行

投稿済みファイルは `posted/` に自動移動されます。

## マークダウンファイルの書き方

```markdown
---
title: "記事タイトル"
category: "nisa"
tags: ["NISA", "投資信託"]
meta_description: "メタディスクリプション（120文字以内）"
affiliate_link: ""
note_link: ""
---

ここから記事本文をマークダウンで記述。

## 見出し

本文テキスト...
```

### フロントマター

| キー | 必須 | 内容 |
|---|---|---|
| title | ○ | 記事タイトル |
| category | ○ | カテゴリスラッグ |
| tags | | タグのリスト |
| meta_description | | メタディスクリプション（空欄なら本文先頭120文字） |
| affiliate_link | | アフィリエイトリンクURL |
| note_link | | note記事のURL |

## カテゴリ対応表

| slug | WP表示名 |
|---|---|
| nisa | NISA・投資信託 |
| sidefire | Side-FIRE・ライフプラン |
| housing | 住宅・マイホーム |
| rakuten | 楽天経済圏 |
| ai | AI・Webツール |
| kids | 子育て・教育費 |
