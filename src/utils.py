import re
import logging
from typing import Optional, Union
import requests
from .config import BOT_TOKEN, CHAT_ID

logger = logging.getLogger("telegram_utils")


def escape_md(text: str) -> str:
    """Escapes Telegram MarkdownV2 special characters."""
    return re.sub(r'([_\*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)


def send_telegram_message(
    message: str,
    keyword_group: Optional[list] = None,
    chat_name: Optional[str] = None,
    parse_mode: Optional[str] = "Markdown"
) -> bool:
    """Sends a text message using the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            if keyword_group and chat_name:
                logger.info(f"MATCH: keyword={keyword_group} | chat={chat_name}")
            return True
        else:
            # If markdown parsing fails, retry without parse_mode
            if parse_mode:
                payload.pop("parse_mode", None)
                retry_resp = requests.post(url, data=payload, timeout=10)
                return retry_resp.status_code == 200
            logger.error(f"Telegram API error: {resp.status_code} - {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram send fail: {type(e).__name__}: {e}")
        return False


def send_telegram_photo(
    caption: str,
    photo: Union[bytes, str],
    target_chat_id: Optional[Union[str, int]] = None,
    parse_mode: Optional[str] = "Markdown"
) -> bool:
    """Sends a photo with a caption using the Telegram Bot API."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    dest_chat = target_chat_id or CHAT_ID
    data = {
        "chat_id": dest_chat,
        "caption": caption
    }
    if parse_mode:
        data["parse_mode"] = parse_mode

    files = {}
    if isinstance(photo, bytes):
        files["photo"] = ("chart.png", photo, "image/png")
    elif isinstance(photo, str):
        with open(photo, "rb") as f:
            photo_bytes = f.read()
        files["photo"] = ("chart.png", photo_bytes, "image/png")
    else:
        raise ValueError("Photo must be bytes or a file path string.")

    try:
        resp = requests.post(url, data=data, files=files, timeout=20)
        if resp.status_code == 200:
            return True
        else:
            if parse_mode:
                data.pop("parse_mode", None)
                if isinstance(photo, bytes):
                    files["photo"] = ("chart.png", photo, "image/png")
                retry_resp = requests.post(url, data=data, files=files, timeout=20)
                return retry_resp.status_code == 200
            logger.error(f"Telegram sendPhoto error: {resp.status_code} - {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram sendPhoto fail: {type(e).__name__}: {e}")
        return False
