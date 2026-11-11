import sys
import asyncio
import threading
import logging
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

from src.config import (
    api_id,
    api_hash,
    phone_number,
    IGNORED_CHATS,
    CHAT_ID,
    STRING_SESSION,
    PORT,
    HEALTHCHECK_ENABLED
)
from src.utils import send_telegram_message, send_telegram_photo
from src.handlers.message_handler import handle_message
from src.handlers.keyword_handler import keyword_console_manager
from src.services.keyword_service import load_keywords
from src.services.stats_service import (
    fetch_price_history,
    calculate_statistics,
    format_stats_report
)
from src.services.chart_service import generate_pricing_chart
from src.services.healthcheck import start_healthcheck_server

# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("telegram_monitor")

# Initialize client using StringSession (for zero-disk cloud hosting) or local session file
if STRING_SESSION:
    logger.info("Initializing Telegram client with TELEGRAM_STRING_SESSION (Cloud Mode).")
    client = TelegramClient(StringSession(STRING_SESSION), api_id, api_hash)
else:
    logger.info("Initializing Telegram client with local session file (new_session.session).")
    client = TelegramClient("new_session", api_id, api_hash)

chat_names = {}  # Runtime cache for chat names


def cache_chat_names(client, chat_names):
    async def _cache():
        async for dialog in client.iter_dialogs():
            chat_id = dialog.id
            chat_name = dialog.title or dialog.name or "Private Chat"
            chat_names[chat_id] = chat_name
            if chat_id not in IGNORED_CHATS:
                logger.info(f"Monitored Chat: [{chat_id}] {chat_name}")
    return _cache


async def handle_stats_command(event):
    """Handles /stats or /report commands received in Telegram."""
    text = (event.message.message or "").strip()
    cmd_prefix = text.split()[0].lower()
    remainder = text[len(cmd_prefix):].strip()

    if not remainder:
        help_text = (
            "ℹ️ *Usage:* `/stats <keyword> [scope]`\n"
            "• *Scopes:* `week` (7 days), `month` (30 days, default), `ever` (all time)\n\n"
            "*Examples:*\n"
            "`/stats rtx 4070`\n"
            "`/stats ar condicionado 12000 week`\n"
            "`/stats ryzen 7 7800x3d ever`"
        )
        send_telegram_message(help_text, chat_name="Command Helper")
        return

    tokens = remainder.split()
    possible_scope = tokens[-1].lower()

    if len(tokens) > 1 and possible_scope in ("ever", "week", "month", "7d", "30d", "all", "semana", "mes", "mês"):
        keyword = " ".join(tokens[:-1])
        scope = possible_scope
    else:
        keyword = remainder
        scope = "month"

    target_chat = event.chat_id if event.chat_id else CHAT_ID
    logger.info(f"Processing stats command for keyword='{keyword}', scope='{scope}' from chat={target_chat}")

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

        # Send photo with markdown caption
        send_telegram_photo(
            caption=report_text,
            photo=chart_bytes,
            target_chat_id=target_chat
        )
    except FloodWaitError as e:
        logger.warning(f"Telegram FloodWait hit. Waiting for {e.seconds} seconds.")
        send_telegram_message(f"⚠️ Telegram rate limit hit. Please retry in {e.seconds} seconds.", chat_name="Stats Query")
    except Exception as e:
        error_msg = f"Failed to process stats command for \"{keyword}\": {e}"
        logger.error(error_msg, exc_info=True)
        send_telegram_message(f"[ERROR] {error_msg}", chat_name="Stats Query")


@client.on(events.NewMessage)
async def handler(event):
    if not event.message or not event.message.message:
        return

    msg_text = event.message.message.strip()

    # Detect stats commands
    if msg_text.startswith(("/stats", "/report", "/grafico", "/precos")):
        await handle_stats_command(event)
        return

    # Process regular message monitoring
    await handle_message(event, chat_names)


async def main():
    # Start background healthcheck HTTP server for cloud deployments
    if HEALTHCHECK_ENABLED:
        await start_healthcheck_server(PORT)

    while True:
        try:
            logger.info("Connecting to Telegram...")
            await client.start(phone=phone_number)

            # Cache and log chat names
            await cache_chat_names(client, chat_names)()

            current_keywords = load_keywords()
            keywords_list = ", ".join(" ".join(group).upper() for group in current_keywords)
            logger.info(f"Monitoring active for {len(current_keywords)} keyword groups: {keywords_list}")

            # Guard interactive console behind sys.stdin.isatty()
            loop = asyncio.get_running_loop()
            if sys.stdin and sys.stdin.isatty():
                logger.info("Terminal detected: starting interactive keyword console manager.")
                threading.Thread(
                    target=keyword_console_manager,
                    args=(client, loop),
                    daemon=True
                ).start()
            else:
                logger.info("Headless/cloud environment detected: interactive console disabled. Controlled via Telegram commands.")

            await client.run_until_disconnected()

        except asyncio.CancelledError:
            logger.info("Process was manually interrupted.")
            send_telegram_message("The Telegram monitoring script was manually interrupted.")
            break
        except FloodWaitError as e:
            logger.warning(f"Telegram FloodWait: sleeping for {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Unexpected bot error: {e}", exc_info=True)
            send_telegram_message(f"The Telegram monitoring script encountered an error: {e}")
            logger.info("Retrying connection in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            logger.info("Shutting down Telegram monitor.")


if __name__ == "__main__":
    asyncio.run(main())
