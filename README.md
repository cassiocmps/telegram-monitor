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

- `keywords.json`: Monitored keywords (managed dynamically via console or directly in JSON)
- `src/config.py`: Your local configuration and credentials (not tracked by git)
- `src/config.example.py`: Example config template (tracked by git)
- `src/utils.py`: Utility functions (send message, send photo, markdown escape)
- `src/bot.py`: Main bot logic, command handler, and event loop
- `src/handlers/message_handler.py`: Message processing, smart matching, and deduplication
- `src/handlers/keyword_handler.py`: Interactive keyword manager and stats runner (console)
- `src/services/text_matcher.py`: Smart token normalization, thousand-dot removal, and word boundary matching
- `src/services/price_parser.py`: Robust currency parsing, unit-price filtering, and installment masking
- `src/services/stats_service.py`: Telegram history querying, statistical aggregations, and Markdown reports
- `src/services/chart_service.py`: Matplotlib visual charts (timeline, benchmarks, and distribution)
- `src/services/dedup_service.py`: Sliding-window alert deduplication to prevent deal spam
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

## Keyword Manager & Price Statistics

While the bot is running, you can manage keywords interactively in the console:

- Select `1` to add a new keyword group (comma separated).
- Select `2` to delete a keyword group by its index.
- Select `3` to list all current keyword groups.
- Select `4` to query price statistics (mean, median, min, max) and generate graphic reports.
- Select `5` to exit the keyword manager and terminate the bot.

All changes are saved to `keywords.json` automatically.

## Price Statistics & Reports

You can query statistics and charts on demand in two ways:

### 1. In the Console Menu
Select option `4` in the terminal menu while the bot is running. Pick any monitored keyword or enter a custom search term, choose the time scope (`week`, `month`, or `ever`), and view formatted metrics with a generated `matplotlib` chart saved to `reports/`. You will also be prompted if you want the report and graphic sent directly to your Telegram chat.

### 2. In Telegram Chat
Send commands directly in your notification chat or to your bot:
- `/stats <keyword>` (defaults to last month)
- `/stats <keyword> week` (last 7 days)
- `/stats <keyword> month` (last 30 days)
- `/stats <keyword> ever` (all time history)

The bot will query Telegram message history on the fly, compute statistics (mean, median, min, max, 25-75% range), generate a visual timeline and distribution chart, and reply with the report photo.

## Notes

- The bot requires Python 3.10+.
