"""
LINE Messaging APIで通知を送信するモジュール
"""

import json
import os

import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"


def notify_line(message):
    """
    LINE Messaging API でプッシュメッセージを送信する。

    Args:
        message: 送信するテキストメッセージ
    """
    access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    user_id = os.environ.get("LINE_USER_ID", "")

    if not access_token or not user_id:
        print("LINE通知: LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が未設定のためスキップ")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message,
            }
        ],
    }

    try:
        resp = requests.post(
            LINE_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30,
        )

        if resp.status_code == 200:
            print("LINE通知: 送信成功")
        else:
            print(f"LINE通知: 送信失敗 (HTTP {resp.status_code}): {resp.text[:300]}")

    except Exception as e:
        print(f"LINE通知: 送信エラー: {e}")
