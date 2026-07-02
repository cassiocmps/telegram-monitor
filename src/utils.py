import re
import requests
from .config import BOT_TOKEN, CHAT_ID

def escape_md(text):
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def send_telegram_message(message, keyword_group, chat_name):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': message
    }
    try:
        requests.post(url, data=payload, timeout=10)
        print(f"[MATCH] keyword={keyword_group} | chat={chat_name}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Telegram send fail: {type(e).__name__}: {e}")
