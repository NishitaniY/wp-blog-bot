"""
WP REST APIで記事を下書き投稿するモジュール
"""

import base64
import os

import requests

# カテゴリスラッグ → 表示名のマッピング
CATEGORY_MAP = {
    "nisa": "NISA・投資信託",
    "sidefire": "Side-FIRE・ライフプラン",
    "housing": "住宅・マイホーム",
    "rakuten": "楽天経済圏",
    "ai": "AI・Webツール",
    "kids": "子育て・教育費",
}


def get_auth_header():
    """Basic認証ヘッダーを生成する。"""
    user = os.environ.get("WP_USER", "")
    password = os.environ.get("WP_APP_PASSWORD", "")
    if not user or not password:
        raise ValueError("WP_USER または WP_APP_PASSWORD が設定されていません")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def get_wp_url():
    """WP_URL を取得する。末尾のスラッシュを除去。"""
    url = os.environ.get("WP_URL", "")
    if not url:
        raise ValueError("WP_URL が設定されていません")
    return url.rstrip("/")


def get_or_create_category(category_slug):
    """
    WP側のカテゴリを検索し、なければ作成する。
    カテゴリIDを返す。
    """
    wp_url = get_wp_url()
    headers = get_auth_header()
    category_name = CATEGORY_MAP.get(category_slug, category_slug)

    # 既存カテゴリを検索
    search_url = f"{wp_url}/wp-json/wp/v2/categories"
    params = {"search": category_name, "per_page": 100}
    resp = requests.get(search_url, headers=headers, params=params, timeout=30)

    if resp.status_code == 200:
        categories = resp.json()
        for cat in categories:
            if cat["name"] == category_name or cat["slug"] == category_slug:
                print(f"カテゴリ発見: {cat['name']} (ID: {cat['id']})")
                return cat["id"], category_name

    # カテゴリが見つからなければ作成
    print(f"カテゴリ '{category_name}' を作成中...")
    create_resp = requests.post(
        search_url,
        headers={**headers, "Content-Type": "application/json"},
        json={"name": category_name, "slug": category_slug},
        timeout=30,
    )

    if create_resp.status_code in (200, 201):
        cat = create_resp.json()
        print(f"カテゴリ作成完了: {cat['name']} (ID: {cat['id']})")
        return cat["id"], category_name
    else:
        print(f"カテゴリ作成失敗: {create_resp.status_code} {create_resp.text}")
        raise RuntimeError(f"カテゴリ作成に失敗しました: {create_resp.status_code}")


def get_or_create_tags(tag_names):
    """
    WP側のタグを検索し、なければ作成する。
    タグIDのリストを返す。
    """
    if not tag_names:
        return []

    wp_url = get_wp_url()
    headers = get_auth_header()
    tag_ids = []

    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        # 既存タグを検索
        search_url = f"{wp_url}/wp-json/wp/v2/tags"
        params = {"search": tag_name, "per_page": 100}
        resp = requests.get(search_url, headers=headers, params=params, timeout=30)

        found = False
        if resp.status_code == 200:
            tags = resp.json()
            for tag in tags:
                if tag["name"] == tag_name:
                    print(f"タグ発見: {tag['name']} (ID: {tag['id']})")
                    tag_ids.append(tag["id"])
                    found = True
                    break

        if not found:
            # タグを作成
            print(f"タグ '{tag_name}' を作成中...")
            create_resp = requests.post(
                search_url,
                headers={**headers, "Content-Type": "application/json"},
                json={"name": tag_name},
                timeout=30,
            )

            if create_resp.status_code in (200, 201):
                tag = create_resp.json()
                print(f"タグ作成完了: {tag['name']} (ID: {tag['id']})")
                tag_ids.append(tag["id"])
            else:
                print(f"タグ作成失敗 '{tag_name}': {create_resp.status_code}")

    return tag_ids


def append_links(content, affiliate_link, note_link):
    """記事本文にアフィリエイトリンク・noteリンクを追加する。"""
    if affiliate_link:
        content += (
            '\n<div class="affiliate-btn-wrap">'
            f'<a href="{affiliate_link}" class="affiliate-btn" '
            'target="_blank" rel="nofollow noopener">詳しくはこちら</a>'
            "</div>"
        )

    if note_link:
        content += (
            '\n<div class="note-link-wrap">'
            "<p>さらに詳しい内容（実際の数字・判断プロセス）はnoteで公開しています。</p>"
            f'<a href="{note_link}" class="affiliate-btn" '
            'target="_blank" rel="noopener">noteで読む</a>'
            "</div>"
        )

    return content


def post_to_wordpress(article, category_slug, affiliate_link="", note_link=""):
    """
    WP REST APIで記事を下書き投稿する。

    Args:
        article: generate_article の戻り値 (dict)
        category_slug: カテゴリスラッグ
        affiliate_link: アフィリエイトリンク (空文字なら無視)
        note_link: noteリンク (空文字なら無視)

    Returns:
        dict: title, preview_url, category_name を含む辞書
    """
    wp_url = get_wp_url()
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    # カテゴリ取得・作成
    category_id, category_name = get_or_create_category(category_slug)

    # タグ取得・作成
    tag_ids = get_or_create_tags(article.get("tags", []))

    # 本文にリンク追加
    content = append_links(article["content"], affiliate_link, note_link)

    # 投稿データ
    post_data = {
        "title": article["title"],
        "content": content,
        "status": "draft",
        "categories": [category_id],
        "tags": tag_ids,
        "meta": {
            "seo_description": article.get("meta_description", ""),
        },
    }

    # 投稿
    post_url = f"{wp_url}/wp-json/wp/v2/posts"
    print(f"WP REST API: POST {post_url}")

    resp = requests.post(post_url, headers=headers, json=post_data, timeout=60)

    if resp.status_code not in (200, 201):
        raise RuntimeError(
            f"WP投稿失敗 (HTTP {resp.status_code}): {resp.text[:500]}"
        )

    post = resp.json()
    post_link = post.get("link", "")
    preview_url = f"{post_link}?preview=true" if post_link else ""

    print(f"投稿成功: ID={post['id']}, タイトル={post['title']['rendered']}")

    return {
        "title": post["title"]["rendered"],
        "preview_url": preview_url,
        "category_name": category_name,
        "post_id": post["id"],
    }
