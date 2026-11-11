import time
import hashlib
from typing import Dict, List, Optional


class AlertDeduplicator:
    """
    Prevents repeated alert spam by maintaining a sliding-window
    time-to-live (TTL) cache of recently alerted deals.
    """

    def __init__(self, cooldown_seconds: int = 7200):
        self.cooldown_seconds = cooldown_seconds
        self._history: Dict[str, float] = {}

    def _cleanup(self, current_time: float):
        expired = [k for k, t in self._history.items() if (current_time - t) > self.cooldown_seconds]
        for k in expired:
            del self._history[k]

    def generate_deal_key(self, keyword_group: List[str], links: List[str], prices: List[float], raw_text: str) -> str:
        """
        Generates a unique signature for a deal based primarily on its URL(s)
        or normalized text and price.
        """
        # If links exist, they are the most reliable unique identifier
        if links and links[0] != "No link found":
            joined_links = "|".join(sorted(links))
            return f"link:{joined_links}"

        # Otherwise hash keyword + prices + short snippet
        kw_part = "-".join(sorted(keyword_group))
        price_part = "-".join(str(p) for p in sorted(prices))
        snippet = "".join(c for c in raw_text.lower() if c.isalnum())[:80]
        payload = f"{kw_part}:{price_part}:{snippet}"
        return f"hash:{hashlib.md5(payload.encode('utf-8')).hexdigest()}"

    def is_duplicate(self, deal_key: str) -> bool:
        """
        Checks if the deal key was already seen within the cooldown window.
        If not seen, marks it as seen and returns False.
        """
        now = time.time()
        self._cleanup(now)

        if deal_key in self._history:
            return True

        self._history[deal_key] = now
        return False


# Global default instance
default_deduplicator = AlertDeduplicator(cooldown_seconds=7200)
