"""
メインスクリプト: drafts/ から記事ファイルを取得 → WP投稿 → posted/ に移動
"""

import glob
import os
import shutil
import sys
import traceback

import yaml
import markdown

from post_to_wp import post_to_wordpress

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DRAFTS_DIR = os.path.join(BASE_DIR, "drafts")
POSTED_DIR = os.path.join(BASE_DIR, "posted")


def get_oldest_draft():
    """drafts/ 内の .md ファイルをアルファベット順で最初の1つ返す。なければ None。"""
    pattern = os.path.join(DRAFTS_DIR, "*.md")
    files = sorted(glob.glob(pattern))
    if not files:
        return None
    return files[0]


def parse_frontmatter(filepath):
    """
    マークダウンファイルを読み込み、YAMLフロントマターと本文を分離する。

    Returns:
        tuple: (metadata: dict, body: str)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # --- で囲まれたフロントマターを分離
    if not content.startswith("---"):
        raise ValueError("フロントマターが見つかりません（先頭が --- で始まっていません）")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError("フロントマターの終了 --- が見つかりません")

    yaml_str = parts[1].strip()
    body = parts[2].strip()

    metadata = yaml.safe_load(yaml_str)
    if not isinstance(metadata, dict):
        raise ValueError("フロントマターのパースに失敗しました")

    # 必須フィールド検証
    if "title" not in metadata:
        raise ValueError("フロントマターに title がありません")
    if "category" not in metadata:
        raise ValueError("フロントマターに category がありません")

    return metadata, body


def convert_md_to_html(md_text):
    """マークダウンをHTMLに変換する。"""
    extensions = ["extra", "codehilite", "toc"]
    extension_configs = {
        "codehilite": {
            "css_class": "highlight",
            "guess_lang": False,
        },
        "toc": {
            "permalink": False,
        },
    }
    html = markdown.markdown(
        md_text,
        extensions=extensions,
        extension_configs=extension_configs,
    )
    return html


def append_links(html, affiliate_link, note_link):
    """本文HTMLの末尾にアフィリエイトリンク・noteリンクを追加する。"""
    if affiliate_link:
        html += (
            '\n<div class="affiliate-btn-wrap">'
            f'<a href="{affiliate_link}" class="affiliate-btn" '
            'target="_blank" rel="nofollow noopener">詳しくはこちら</a>'
            "</div>"
        )

    if note_link:
        html += (
            '\n<div class="note-link-wrap">'
            "<p>さらに詳しい内容（実際の数字・判断プロセス）はnoteで公開しています。</p>"
            f'<a href="{note_link}" class="affiliate-btn" '
            'target="_blank" rel="noopener">noteで読む</a>'
            "</div>"
        )

    return html


def generate_meta_description(metadata, body):
    """meta_description がなければ本文先頭120文字を使用する。"""
    desc = metadata.get("meta_description", "")
    if desc:
        return desc
    # マークダウン記法を除去した簡易テキストから120文字
    import re
    plain = re.sub(r"[#*\[\]`>_~\-|]", "", body)
    plain = re.sub(r"\n+", " ", plain).strip()
    return plain[:120]


def move_to_posted(filepath):
    """ファイルを drafts/ から posted/ に移動する。"""
    filename = os.path.basename(filepath)
    dest = os.path.join(POSTED_DIR, filename)
    shutil.move(filepath, dest)
    print(f"ファイル移動: {filepath} → {dest}")


def main():
    print("=== WP Auto Post: 開始 ===")

    # 1. drafts/ から記事ファイルを取得
    filepath = get_oldest_draft()
    if filepath is None:
        print("投稿する記事がありません。終了します。")
        sys.exit(0)

    filename = os.path.basename(filepath)
    print(f"対象ファイル: {filename}")

    # 2. フロントマターと本文を分離
    try:
        metadata, body = parse_frontmatter(filepath)
        print(f"タイトル: {metadata['title']}")
        print(f"カテゴリ: {metadata['category']}")
    except Exception as e:
        print(f"ファイル解析エラー: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    # 3. マークダウン → HTML変換
    try:
        html_content = convert_md_to_html(body)
        print(f"HTML変換完了 ({len(html_content)} 文字)")
    except Exception as e:
        print(f"マークダウン変換エラー: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    # 4. リンク挿入
    affiliate_link = metadata.get("affiliate_link", "") or ""
    note_link = metadata.get("note_link", "") or ""
    html_content = append_links(html_content, affiliate_link.strip(), note_link.strip())

    # 5. meta_description 生成
    meta_description = generate_meta_description(metadata, body)

    # 6. 記事データ組み立て
    article = {
        "title": metadata["title"],
        "content": html_content,
        "meta_description": meta_description,
        "tags": metadata.get("tags", []) or [],
    }

    # 7. WP REST APIで下書き投稿
    try:
        print("WordPressに投稿中...")
        result = post_to_wordpress(
            article=article,
            category_slug=metadata["category"],
        )
        print(f"投稿完了: {result['title']}")
        print(f"投稿ID: {result['post_id']}")
        print(f"URL: {result['url']}")
    except Exception as e:
        print(f"WP投稿エラー: {e}\n{traceback.format_exc()}")
        sys.exit(1)

    # 8. ファイルを posted/ に移動
    try:
        move_to_posted(filepath)
    except Exception as e:
        print(f"ファイル移動エラー（投稿自体は成功）: {e}")

    print("=== WP Auto Post: 完了 ===")


if __name__ == "__main__":
    main()
