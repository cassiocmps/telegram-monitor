import asyncio
import threading
import shlex
from telethon import TelegramClient, events

from src.config import api_id, api_hash, phone_number, IGNORED_CHATS, CHAT_ID
from src.utils import send_telegram_message, send_telegram_photo
from src.handlers.message_handler import handle_message
from src.handlers.keyword_handler import keyword_console_manager
from src.services.keyword_service import load_keywords
from src.services.stats_service import (
    fetch_price_history,
    calculate_statistics,
    format_stats_report,
    parse_time_scope
)
from src.services.chart_service import generate_pricing_chart

client = TelegramClient('new_session', api_id, api_hash)
chat_names = {}  # Runtime dictionary to cache chat names


def cache_chat_names(client, chat_names):
    async def _cache():
        async for dialog in client.iter_dialogs():
            chat_id = dialog.id
            chat_name = dialog.title or dialog.name or "Private Chat"
            chat_names[chat_id] = chat_name
            if chat_id not in IGNORED_CHATS:
                print(f"Chat ID: {chat_id}, Chat Name: {chat_name}.")
    return _cache


async def handle_stats_command(event):
    """Handles /stats or /report commands received in Telegram."""
    text = (event.message.message or "").strip()
    # Normalize command
    cmd_prefix = text.split()[0].lower()
    remainder = text[len(cmd_prefix):].strip()

    if not remainder:
        help_text = (
            "ℹ️ *Usage:* `/stats <keyword> [scope]`\n"
            "• *Scopes:* `week` (7 days), `month` (30 days, default), `ever` (all time)\n\n"
            "*Examples:*\n"
            "`/stats rtx 4070`\n"
            "`/stats rtx 4070 week`\n"
            "`/stats ryzen 7 7800x3d ever`"
        )
        send_telegram_message(help_text, chat_name="Command Helper")
        return

    # Check if the last word is a known time scope
    tokens = remainder.split()
    possible_scope = tokens[-1].lower()
    
    if len(tokens) > 1 and possible_scope in ("ever", "week", "month", "7d", "30d", "all", "semana", "mes", "mês"):
        keyword = " ".join(tokens[:-1])
        scope = possible_scope
    else:
        keyword = remainder
        scope = "month"

    target_chat = event.chat_id if event.chat_id else CHAT_ID

    status_msg = f"🔍 Searching Telegram offers for \"*{keyword}*\" ({scope})... Please wait."
    send_telegram_message(status_msg, chat_name="Stats Query")

    try:
        records, scope_label = await fetch_price_history(client, keyword, scope=scope)
        if not records:
            empty_msg = f"⚠️ No price records found for \"*{keyword}*\" within {scope_label.lower()}."
            send_telegram_message(empty_msg, chat_name="Stats Query")
            return

        stats = calculate_statistics(records)
        report_text = format_stats_report(stats, keyword, scope_label)

        # Generate chart
        chart_bytes = generate_pricing_chart(
            keyword=keyword,
            scope_label=scope_label,
            records=records,
            stats=stats
        )

        # Send photo with markdown caption to Telegram
        send_telegram_photo(
            caption=report_text,
            photo=chart_bytes,
            target_chat_id=target_chat
        )
    except Exception as e:
        error_msg = f"[ERROR] Failed to process stats command for \"{keyword}\": {e}"
        print(error_msg)
        send_telegram_message(error_msg, chat_name="Stats Query")


@client.on(events.NewMessage)
async def handler(event):
    if not event.message or not event.message.message:
        return

    msg_text = event.message.message.strip()

    # Detect stats commands
    if msg_text.startswith(("/stats", "/report", "/grafico", "/precos")):
        await handle_stats_command(event)
        return

    # Otherwise process regular message monitoring
    await handle_message(event, chat_names)


async def main():
    while True:
        try:
            print("Starting Telegram client...")
            await client.start(phone=phone_number)

            # Log and cache all chat names
            await cache_chat_names(client, chat_names)()

            current_keywords = load_keywords()
            keywords_list = ", ".join(" ".join(group).upper() for group in current_keywords)
            print(f"Monitoring for keywords: {keywords_list}.")

            # Start the keyword console manager in a separate thread with event loop access
            loop = asyncio.get_running_loop()
            threading.Thread(
                target=keyword_console_manager,
                args=(client, loop),
                daemon=True
            ).start()

            await client.run_until_disconnected()

        except asyncio.CancelledError:
            print("Process was manually interrupted.")
            send_telegram_message("The Telegram monitoring script was manually interrupted.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            send_telegram_message(f"The Telegram monitoring script encountered an error: {e}")
            print("Retrying connection in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            print("Shutting down the script.")
            send_telegram_message("The Telegram monitoring script has been stopped or interrupted.")


if __name__ == "__main__":
    asyncio.run(main())
