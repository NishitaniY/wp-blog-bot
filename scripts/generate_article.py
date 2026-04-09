"""
Claude APIを使った記事生成モジュール
"""

import json
import os
import re

import anthropic

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "article_prompt.txt")


def load_prompt_template():
    """プロンプトテンプレートを読み込む。"""
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def parse_json_response(text):
    """
    Claude APIのレスポンスからJSONをパースする。
    ```json ... ``` で囲まれている場合はそれを除去してからパースする。
    パース失敗時はフォールバックとしてcontent扱いにする。
    """
    # ```json ... ``` ブロックを抽出
    match = re.search(r"```json\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
    else:
        json_str = text.strip()

    try:
        data = json.loads(json_str)

        # 必須フィールドの検証
        if "title" not in data or "content" not in data:
            raise ValueError("title または content が見つかりません")

        # デフォルト値の設定
        data.setdefault("meta_description", "")
        data.setdefault("tags", [])

        return data

    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSONパース失敗 ({e}), フォールバック処理を実行")
        return {
            "title": "無題の記事",
            "meta_description": "",
            "content": text,
            "tags": [],
        }


def generate_article(keyword, category):
    """
    Claude APIで記事を生成する。

    Args:
        keyword: 記事のキーワード
        category: カテゴリスラッグ

    Returns:
        dict: title, meta_description, content, tags を含む辞書
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY が設定されていません")

    # プロンプト構築
    template = load_prompt_template()
    prompt = template.replace("{keyword}", keyword).replace("{category}", category)

    print(f"Claude API 呼び出し中 (キーワード: {keyword})")

    # Claude API呼び出し
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    # レスポンス取得
    response_text = message.content[0].text
    print(f"Claude API レスポンス受信 ({len(response_text)} 文字)")

    # JSONパース
    article = parse_json_response(response_text)
    print(f"記事パース完了: 「{article['title']}」")

    return article
