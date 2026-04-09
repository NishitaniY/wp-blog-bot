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
    WP側のカテゴリをスラッグで検索し、なければ作成する。
    カテゴリIDと名前を返す。
    """
    wp_url = get_wp_url()
    headers = get_auth_header()
    category_name = CATEGORY_MAP.get(category_slug, category_slug)

    # スラッグで検索
    search_url = f"{wp_url}/wp-json/wp/v2/categories"
    params = {"slug": category_slug}
    resp = requests.get(search_url, headers=headers, params=params, timeout=30)

    if resp.status_code == 200 and resp.json():
        cat = resp.json()[0]
        print(f"カテゴリ発見: {cat['name']} (ID: {cat['id']})")
        return cat["id"], cat["name"]

    # 見つからなければ作成
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
        return cat["id"], cat["name"]
    else:
        raise RuntimeError(
            f"カテゴリ作成に失敗 (HTTP {create_resp.status_code}): {create_resp.text[:300]}"
        )


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
        tag_name = str(tag_name).strip()
        if not tag_name:
            continue

        # 検索
        search_url = f"{wp_url}/wp-json/wp/v2/tags"
        params = {"search": tag_name, "per_page": 100}
        resp = requests.get(search_url, headers=headers, params=params, timeout=30)

        found = False
        if resp.status_code == 200:
            for tag in resp.json():
                if tag["name"] == tag_name:
                    print(f"タグ発見: {tag['name']} (ID: {tag['id']})")
                    tag_ids.append(tag["id"])
                    found = True
                    break

        if not found:
            # 作成
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


def post_to_wordpress(article, category_slug):
    """
    WP REST APIで記事を下書き投稿する。

    Args:
        article: dict (title, content, meta_description, tags)
        category_slug: カテゴリスラッグ

    Returns:
        dict: title, url, post_id
    """
    wp_url = get_wp_url()
    headers = get_auth_header()
    headers["Content-Type"] = "application/json"

    # カテゴリ取得・作成
    category_id, category_name = get_or_create_category(category_slug)

    # タグ取得・作成
    tag_ids = get_or_create_tags(article.get("tags", []))

    # 投稿データ
    post_data = {
        "title": article["title"],
        "content": article["content"],
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
    print(f"投稿成功: ID={post['id']}, タイトル={post['title']['rendered']}")

    return {
        "title": post["title"]["rendered"],
        "url": post.get("link", ""),
        "post_id": post["id"],
    }
