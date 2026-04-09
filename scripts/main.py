"""
メインスクリプト: キーワード取得 → 記事生成 → WP投稿 → LINE通知
"""

import csv
import os
import sys
import traceback

from generate_article import generate_article
from post_to_wp import post_to_wordpress
from notify_line import notify_line

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "keywords.csv")


def read_keywords():
    """keywords.csv を読み込み、全行をリストで返す。"""
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    return fieldnames, rows


def write_keywords(fieldnames, rows):
    """keywords.csv を上書き保存する。"""
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_pending(rows):
    """status=pending の最初の行のインデックスを返す。なければ -1。"""
    for i, row in enumerate(rows):
        if row.get("status", "").strip() == "pending":
            return i
    return -1


def main():
    print("=== WP Auto Post: 開始 ===")

    # 1. CSV読み込み
    try:
        fieldnames, rows = read_keywords()
        print(f"CSV読み込み完了: {len(rows)} 行")
    except Exception as e:
        print(f"CSV読み込みエラー: {e}")
        notify_line(f"❌ CSV読み込みに失敗しました\n\nエラー: {e}")
        sys.exit(1)

    # 2. pending行を取得
    idx = find_pending(rows)
    if idx == -1:
        print("pending のキーワードがありません")
        notify_line(
            "📭 投稿するキーワードがありません。\n"
            "keywords.csv にキーワードを追加してください。"
        )
        sys.exit(0)

    target = rows[idx]
    keyword = target["keyword"].strip()
    category = target["category"].strip()
    affiliate_link = target.get("affiliate_link", "").strip()
    note_link = target.get("note_link", "").strip()
    print(f"対象キーワード: {keyword} (カテゴリ: {category})")

    # 3. Claude APIで記事生成
    try:
        print("記事を生成中...")
        article = generate_article(keyword, category)
        print(f"記事生成完了: {article['title']}")
    except Exception as e:
        error_msg = f"記事生成エラー: {e}\n{traceback.format_exc()}"
        print(error_msg)
        notify_line(
            f"❌ 投稿に失敗しました\n\n"
            f"キーワード: {keyword}\n"
            f"エラー: {e}"
        )
        sys.exit(1)

    # 4. WP REST APIで下書き投稿
    try:
        print("WordPressに投稿中...")
        result = post_to_wordpress(
            article=article,
            category_slug=category,
            affiliate_link=affiliate_link,
            note_link=note_link,
        )
        print(f"投稿完了: {result['title']}")
        print(f"プレビューURL: {result['preview_url']}")
    except Exception as e:
        error_msg = f"WP投稿エラー: {e}\n{traceback.format_exc()}"
        print(error_msg)
        notify_line(
            f"❌ 投稿に失敗しました\n\n"
            f"キーワード: {keyword}\n"
            f"エラー: {e}"
        )
        sys.exit(1)

    # 5. LINE通知
    try:
        notify_line(
            f"📝 下書き投稿しました\n\n"
            f"タイトル: {result['title']}\n"
            f"カテゴリ: {result['category_name']}\n"
            f"キーワード: {keyword}\n\n"
            f"▼ 確認・編集\n"
            f"{result['preview_url']}"
        )
        print("LINE通知完了")
    except Exception as e:
        print(f"LINE通知エラー（投稿自体は成功）: {e}")

    # 6. CSV更新
    rows[idx]["status"] = "posted"
    write_keywords(fieldnames, rows)
    print("CSV更新完了")

    print("=== WP Auto Post: 完了 ===")


if __name__ == "__main__":
    main()
