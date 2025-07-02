# Your Telegram API ID (get from https://my.telegram.org)
api_id = ''  # int: Telegram API ID

# Your Telegram API hash (get from https://my.telegram.org)
api_hash = ''  # str: Telegram API hash

# Your phone number associated with Telegram
phone_number = ''  # str: Telegram phone number

# Telegram Bot Token (get from BotFather)
BOT_TOKEN = ''  # str: Telegram Bot Token

# Chat ID to send notifications to
CHAT_ID = ''  # str or int: Target chat ID

# List of chat IDs to ignore
IGNORED_CHATS = []  # list: Chats to ignore

# List of keyword groups to monitor (each group is a list of words)
keywords = [
    # Example: ['RTX 4070'], ['ar condicionado', 'quente']
]

# List of message substrings to ignore (exceptions)
EXCEPTION_SUBSTRINGS = [
    # Example: 'notebook'
]
