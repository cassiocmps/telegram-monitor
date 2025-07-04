# Telegram Monitor Bot

This project monitors Telegram groups for specific keywords and forwards relevant messages to a designated chat using a bot.

## Configuration

You should keep your real `config.py` out of version control. Use `src/config.example.py` as a template.

- `api_id`, `api_hash`, `phone_number`: Your Telegram API credentials
- `BOT_TOKEN`: Your Telegram bot token
- `CHAT_ID`: The chat ID to receive notifications
- `IGNORED_CHATS`: List of chat IDs to ignore
- `keywords`: List of keyword groups to monitor (each group is a list of words)
- `EXCEPTION_SUBSTRINGS`: List of message substrings to ignore

## Structure

- `src/config.py`: Your local configuration (not tracked by git)
- `src/config.example.py`: Example config template (tracked by git)
- `src/utils.py`: Utility functions (send message, markdown escape)
- `src/bot.py`: Main bot logic and event loop
- `src/handlers/message_handler.py`: Message processing logic
- `src/handlers/keyword_handler.py`: Interactive keyword manager (console)
- `requirements.txt`: Python dependencies

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Copy the example config and fill in your credentials:
   ```bash
   cp src/config.example.py src/config.py
   # Then edit src/config.py with your credentials and settings
   ```
3. Run the bot from the project root:
   ```bash
   python -m src.bot
   ```

## Keyword Manager

While the bot is running, you can manage keywords interactively in the console:

- Select `1` to add a new keyword group (comma separated).
- Select `2` to delete a keyword group by its index.
- Select `3` to list all current keyword groups.
- Select `4` to exit the keyword manager and terminate the bot.

All changes are saved to `src/config.py` automatically.

## Notes

- The bot requires Python 3.10+.
