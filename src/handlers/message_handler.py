import re
from ..config import keywords, IGNORED_CHATS, EXCEPTION_SUBSTRINGS
from ..utils import send_telegram_message

def extract_price(message: str) -> str:
    value_matches = re.findall(r'\$\s?(\d+[.,]?\d*)', message)
    if not value_matches:
        return "N/A"
    prices = [float(v.replace('.', '').replace(',', '.')) for v in value_matches]
    min_price = min(prices)
    return str(min_price)

def extract_links(message: str) -> str:
    links = re.findall(r'(https?://[^\s]+)', message)
    return "\n".join(links) if links else "No link found"

def build_message(keyword_group, value, product_links, chat_name, msg_link) -> str:
    keyword_label = " ".join(keyword_group).upper()
    return f"{keyword_label} R${value}\n{product_links}\n\n{chat_name}\n{msg_link}"

async def handle_message(event, chat_names):
    if event.chat_id in IGNORED_CHATS:
        return

    message = event.message.message.lower()

    if any(substr in message for substr in EXCEPTION_SUBSTRINGS):
        return

    chat_id = event.chat_id
    chat_name = chat_names.get(chat_id, "Unknown Chat")
    # If chat_name is 'Unknown Chat', this is likely a reply message or from an unknown chat and should not be considered
    if chat_name == "Unknown Chat":
        return

    normalized_message = message.replace('-', ' ')
    for keyword_group in keywords:
        if all(word.lower() in normalized_message for word in keyword_group):
            value = extract_price(message)
            product_links = extract_links(event.message.message)
            
            msg_link = f"https://t.me/c/{str(chat_id)[4:]}/{event.message.id}" if str(chat_id).startswith("-100") else "Link unavailable"
            text = build_message(keyword_group, value, product_links, chat_name, msg_link)
            
            send_telegram_message(text)
            return
