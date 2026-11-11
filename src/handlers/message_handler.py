import re
import logging
from typing import List, Tuple
from ..config import IGNORED_CHATS, EXCEPTION_SUBSTRINGS
from ..utils import send_telegram_message
from ..services.price_parser import extract_prices_with_values
from ..services.text_matcher import matches_keyword_group, contains_any_exception
from ..services.dedup_service import default_deduplicator
from ..services.keyword_service import load_keywords

logger = logging.getLogger("message_handler")


def extract_links(message: str) -> List[str]:
    links = re.findall(r'(https?://[^\s]+)', message)
    return links if links else []


def build_message(keyword_group: List[str], value_pairs: List[Tuple[str, float]], product_links: List[str], chat_name: str, msg_link: str) -> str:
    keyword_label = " ".join(keyword_group).upper()
    if value_pairs:
        prices_str = ', '.join([f'R$ {raw}' for raw, _ in value_pairs])
        if len(value_pairs) > 1:
            cheapest = min(value_pairs, key=lambda x: x[1])
            prices_str += f" (Lowest: R$ {cheapest[0]})"
    else:
        prices_str = 'N/A'
    
    links_str = "\n".join(product_links) if product_links else "No link found"
    return f"{keyword_label} {prices_str}\n{links_str}\n\n{chat_name}\n{msg_link}"


async def handle_message(event, chat_names):
    if not event.message or not event.message.message:
        return

    if event.chat_id in IGNORED_CHATS:
        return

    raw_message = event.message.message

    # Check for exceptions using smart word-boundary matching
    if contains_any_exception(raw_message, EXCEPTION_SUBSTRINGS):
        return

    chat_id = event.chat_id
    chat_name = chat_names.get(chat_id, "Unknown Chat")
    if chat_name == "Unknown Chat":
        return

    # Dynamically fetch current keywords
    current_keywords = load_keywords()

    for keyword_group in current_keywords:
        if matches_keyword_group(raw_message, keyword_group):
            value_pairs = extract_prices_with_values(raw_message)
            product_links = extract_links(raw_message)
            numeric_prices = [p[1] for p in value_pairs]

            # Check deduplication cooldown window
            deal_key = default_deduplicator.generate_deal_key(
                keyword_group=keyword_group,
                links=product_links,
                prices=numeric_prices,
                raw_text=raw_message
            )
            if default_deduplicator.is_duplicate(deal_key):
                logger.info(f"DEDUP: Suppressed duplicate alert for '{' '.join(keyword_group)}' in {chat_name}")
                return

            msg_link = f"https://t.me/c/{str(chat_id)[4:]}/{event.message.id}" if str(chat_id).startswith("-100") else "Link unavailable"
            text = build_message(keyword_group, value_pairs, product_links, chat_name, msg_link)

            send_telegram_message(text, keyword_group, chat_name)
            return
