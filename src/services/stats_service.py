import re
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple

from telethon import TelegramClient

from .price_parser import extract_prices_with_values
from ..config import IGNORED_CHATS, EXCEPTION_SUBSTRINGS, CHAT_ID


def parse_time_scope(scope_str: Optional[str]) -> Tuple[Optional[datetime], str]:
    """
    Parses a scope string (e.g. 'week', 'month', 'ever', '7d')
    into a UTC cutoff datetime and a human-readable label.
    """
    if not scope_str:
        # Default to last 30 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        return cutoff, "Last Month"

    scope_lower = scope_str.strip().lower()

    if scope_lower in ("ever", "all", "all_time", "all-time", "sempre", "tudo"):
        return None, "All Time"

    if scope_lower in ("week", "last_week", "last-week", "last week", "7d", "semana"):
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        return cutoff, "Last Week"

    if scope_lower in ("month", "last_month", "last-month", "last month", "30d", "mes", "mês"):
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        return cutoff, "Last Month"

    # Match custom days, e.g. "14d" or "60 days"
    days_match = re.match(r"^(\d+)\s*(?:d|days|dias)?$", scope_lower)
    if days_match:
        days = int(days_match.group(1))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return cutoff, f"Last {days} Days"

    # Default fallback
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    return cutoff, "Last Month"


async def fetch_price_history(
    client: TelegramClient,
    keyword: str,
    scope: str = "month",
    include_destination_chat: bool = True,
    max_messages_per_chat: int = 150
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Directly queries Telegram dialogs and messages for the given keyword
    within the designated time scope.
    
    Returns (records_list, scope_label).
    """
    cutoff_dt, scope_label = parse_time_scope(scope)
    records: List[Dict[str, Any]] = []
    seen_message_keys = set()

    # Split keyword terms for matching verification
    keyword_terms = [t.lower() for t in keyword.split() if t.strip()]

    target_dialogs = []

    # Include destination notification chat if configured
    if include_destination_chat and CHAT_ID:
        try:
            dest_entity = await client.get_entity(int(CHAT_ID) if str(CHAT_ID).lstrip("-").isdigit() else CHAT_ID)
            target_dialogs.append(dest_entity)
        except Exception:
            pass

    # Collect other monitored dialogs
    async for dialog in client.iter_dialogs():
        if dialog.id in IGNORED_CHATS:
            continue
        if target_dialogs and dialog.id == getattr(target_dialogs[0], "id", None):
            continue
        target_dialogs.append(dialog)

    for dialog in target_dialogs:
        dialog_id = getattr(dialog, "id", None)
        dialog_title = getattr(dialog, "title", None) or getattr(dialog, "name", None) or "Telegram Chat"

        try:
            # Query Telegram using server-side search
            async for msg in client.iter_messages(dialog, search=keyword, limit=max_messages_per_chat):
                if not msg or not msg.message:
                    continue

                # Messages arrive newest first; stop if older than cutoff
                if cutoff_dt and msg.date:
                    msg_date_utc = msg.date if msg.date.tzinfo else msg.date.replace(tzinfo=timezone.utc)
                    if msg_date_utc < cutoff_dt:
                        break

                raw_text = msg.message
                lower_text = raw_text.lower().replace("-", " ")

                # Verify all keyword terms appear in the message
                if not all(term in lower_text for term in keyword_terms):
                    continue

                # Filter out exceptions
                if any(substr.lower() in lower_text for substr in EXCEPTION_SUBSTRINGS):
                    continue

                # Extract prices
                extracted = extract_prices_with_values(raw_text)
                if not extracted:
                    continue

                msg_link = ""
                if str(dialog_id).startswith("-100"):
                    clean_id = str(dialog_id)[4:]
                    msg_link = f"https://t.me/c/{clean_id}/{msg.id}"

                msg_date = msg.date if msg.date else datetime.now(timezone.utc)

                for raw_price_str, numeric_price in extracted:
                    dedup_key = (dialog_id, msg.id, numeric_price)
                    if dedup_key in seen_message_keys:
                        continue
                    seen_message_keys.add(dedup_key)

                    records.append({
                        "chat_id": dialog_id,
                        "chat_name": dialog_title,
                        "message_id": msg.id,
                        "timestamp": msg_date,
                        "price": numeric_price,
                        "raw_price": raw_price_str,
                        "message_text": raw_text,
                        "message_link": msg_link
                    })

        except Exception as e:
            # Continue checking other chats even if one fails or encounters permission limits
            print(f"[STATS] Error querying chat {dialog_title}: {e}")
            continue

    return records, scope_label


def calculate_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates statistical metrics from a list of price records."""
    if not records:
        return {"count": 0}

    prices = [r["price"] for r in records]
    prices_sorted = sorted(prices)
    count = len(prices)

    mean_price = sum(prices) / count
    median_price = statistics.median(prices)
    min_price = min(prices)
    max_price = max(prices)
    std_dev = statistics.stdev(prices) if count > 1 else 0.0

    # Percentiles
    if count >= 4:
        quartiles = statistics.quantiles(prices, n=4)
        q25, q75 = quartiles[0], quartiles[2]
    else:
        q25 = min_price
        q75 = max_price

    # Find cheapest deal and latest deal
    cheapest_record = min(records, key=lambda r: r["price"])
    latest_record = max(records, key=lambda r: r["timestamp"])

    return {
        "count": count,
        "mean": mean_price,
        "median": median_price,
        "min": min_price,
        "max": max_price,
        "std_dev": std_dev,
        "q25": q25,
        "q75": q75,
        "cheapest_record": cheapest_record,
        "latest_record": latest_record,
    }


def format_stats_report(stats: Dict[str, Any], keyword: str, scope_label: str) -> str:
    """Formats calculated statistics into a Telegram/console markdown message."""
    count = stats.get("count", 0)
    if count == 0:
        return (
            f"🔍 *Price Statistics: {keyword.upper()}*\n"
            f"🕒 *Time Scope:* {scope_label}\n\n"
            f"No pricing records found for \"{keyword}\" within {scope_label.lower()}."
        )

    mean_val = stats["mean"]
    median_val = stats["median"]
    min_val = stats["min"]
    max_val = stats["max"]
    q25 = stats["q25"]
    q75 = stats["q75"]
    cheapest = stats["cheapest_record"]
    latest = stats["latest_record"]

    # Calculate difference between latest price and median
    latest_price = latest["price"]
    diff_pct = ((latest_price - median_val) / median_val) * 100
    diff_str = f"{'+' if diff_pct > 0 else ''}{diff_pct:.1f}% vs median"

    # Calculate discount percentage of the lowest price compared to median
    min_discount_pct = ((median_val - min_val) / median_val) * 100 if median_val > 0 else 0.0
    min_discount_str = f"({min_discount_pct:.1f}% below median)" if min_discount_pct > 0 else "(at median)"
    min_date_str = cheapest["timestamp"].strftime("%d/%m/%Y %H:%M")

    report_lines = [
        f"📊 *Price Statistics: {keyword.upper()}*",
        f"🕒 *Scope:* {scope_label} | *Samples:* {count}",
        "",
        f"🔥 *Lowest Price (Menor Preço):* R$ {min_val:,.2f} {min_discount_str}",
        f"   • *Date:* {min_date_str}",
        f"   • *Chat:* {cheapest['chat_name']}",
        "",
        f"💰 *Median (Mediana):* R$ {median_val:,.2f}",
        f"📈 *Average (Média):* R$ {mean_val:,.2f}",
        f"🔺 *Highest (Máximo):* R$ {max_val:,.2f}",
        f"🎯 *25% - 75% Range:* R$ {q25:,.2f} - R$ {q75:,.2f}",
        "",
        f"🏷️ *Latest Offer:* R$ {latest_price:,.2f} ({diff_str})"
    ]

    if cheapest.get("message_link"):
        report_lines.append(f"🔗 [View Lowest Price Deal]({cheapest['message_link']})")

    return "\n".join(report_lines)
