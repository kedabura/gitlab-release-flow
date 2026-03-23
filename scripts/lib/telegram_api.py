import requests

from lib.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram_message(text, verbose=False):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("telegram is not configured, skip notification")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=30)
    if verbose:
        print(f"telegram status={response.status_code}")
        print(f"telegram body={response.text}")
    response.raise_for_status()