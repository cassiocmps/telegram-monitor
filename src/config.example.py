import os
import json


def _load_env_file(filepath: str):
    """Simple zero-dependency .env file loader."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


# Try loading .env from project root
_project_root = os.path.dirname(os.path.dirname(__file__))
_load_env_file(os.path.join(_project_root, ".env"))

# 12-Factor Environment Variable Resolution (preferred for cloud hosting)
api_id = int(os.getenv('TELEGRAM_API_ID', 0))
api_hash = os.getenv('TELEGRAM_API_HASH', '')
phone_number = os.getenv('TELEGRAM_PHONE_NUMBER', '')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Optional Telethon StringSession (enables zero-disk deployment on cloud free tiers like Render / Railway)
STRING_SESSION = os.getenv('TELEGRAM_STRING_SESSION', '')

# Ignored chats parsing (JSON list or comma-separated numbers)
_env_ignored = os.getenv('IGNORED_CHATS')
if _env_ignored:
    try:
        IGNORED_CHATS = json.loads(_env_ignored)
    except Exception:
        IGNORED_CHATS = [int(cid.strip()) for cid in _env_ignored.split(',') if cid.strip().lstrip('-').isdigit()]
else:
    IGNORED_CHATS = []

# Exception substrings parsing
_env_exceptions = os.getenv('EXCEPTION_SUBSTRINGS')
if _env_exceptions:
    try:
        EXCEPTION_SUBSTRINGS = json.loads(_env_exceptions)
    except Exception:
        EXCEPTION_SUBSTRINGS = [s.strip() for s in _env_exceptions.split(',') if s.strip()]
else:
    EXCEPTION_SUBSTRINGS = []

# Fallback keywords if keywords.json is absent
keywords = [
    # ['RTX 4070'], ['ar condicionado', '12000']
]

# Cloud web healthcheck port
PORT = int(os.getenv('PORT', '8080'))
HEALTHCHECK_ENABLED = os.getenv('HEALTHCHECK_ENABLED', 'true').lower() in ('true', '1', 'yes')
