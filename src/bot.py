from telethon import TelegramClient, events
import asyncio
import threading
from src.config import api_id, api_hash, phone_number, keywords, IGNORED_CHATS
from src.utils import send_telegram_message
from src.handlers.message_handler import handle_message
from src.handlers.keyword_handler import keyword_console_manager

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

@client.on(events.NewMessage)
async def handler(event):
    await handle_message(event, chat_names)

async def main():
    while True:
        try:
            print("Starting Telegram client...")
            await client.start(phone=phone_number)

            # Log and cache all chat names
            await cache_chat_names(client, chat_names)()

            keywords_list = ", ".join(" ".join(group).upper() for group in keywords)
            print(f"Monitoring for keywords: {keywords_list}.")

            # Start the keyword manager in a separate thread after the bot is running
            threading.Thread(target=keyword_console_manager, daemon=True).start()

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
