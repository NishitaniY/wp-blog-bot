# wp-blog-bot

GitHub Actions + Claude API + WP REST API を使ったブログ記事の自動生成・投稿パイプライン。

## セットアップ

### 1. GitHub Secrets に以下を登録

| Secret名 | 説明 |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API キー |
| `WP_URL` | WordPressサイトURL（例: `https://example.com`） |
| `WP_USER` | WP管理者ユーザー名 |
| `WP_APP_PASSWORD` | WPアプリケーションパスワード |
| `LINE_ACCESS_TOKEN` | LINE Messaging API チャネルアクセストークン |
| `LINE_USER_ID` | LINE通知先のユーザーID |

### 2. WPアプリケーションパスワードの取得

WP管理画面 → ユーザー → プロフィール → アプリケーションパスワード から発行。

### 3. keywords.csv にキーワードを追加

```csv
keyword,category,affiliate_link,note_link,status
NISA 新NISA 始め方 2026,nisa,,,pending
```

## 使い方

- **自動実行**: 毎週月曜 7:00 JST に pending の最初の1件を処理
- **手動実行**: Actions → WP Auto Post → Run workflow

## カテゴリ対応表

| slug | WP表示名 |
|---|---|
| nisa | NISA・投資信託 |
| sidefire | Side-FIRE・ライフプラン |
| housing | 住宅・マイホーム |
| rakuten | 楽天経済圏 |
| ai | AI・Webツール |
| kids | 子育て・教育費 |
