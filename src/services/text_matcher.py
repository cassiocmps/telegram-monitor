import re
import unicodedata
from typing import List, Union


def remove_accents(text: str) -> str:
    """Removes diacritics and accents (e.g., 'lenço' -> 'lenco', 'mês' -> 'mes')."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    """
    Normalizes text for robust product and deal matching:
    1. Lowercase and accent removal
    2. Number thousand-separator normalization: '12.000' -> '12000', '1.499' -> '1499'
    3. Alphanumeric transition spacing: '12000btu' -> '12000 btu', '9070xt' -> '9070 xt'
    4. Hyphens and punctuation to spaces
    5. Clean excess whitespace
    """
    if not text:
        return ""

    # Convert to lowercase and strip accents
    s = remove_accents(text.lower())

    # Replace hyphens and underscores with spaces
    s = s.replace("-", " ").replace("_", " ")

    # Normalize numbers with thousand dots/commas: e.g. 12.000 -> 12000, 1.499 -> 1499
    # Matches digit groups separated by dots or commas where followed by 3 digits
    s = re.sub(r'(?<=\d)[.,](?=\d{3}(?!\d))', '', s)

    # Separate letter-digit and digit-letter transitions so '9070xt' -> '9070 xt', '12000btu' -> '12000 btu'
    s = re.sub(r'(\d+)([a-zA-Z]+)', r'\1 \2', s)
    s = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', s)

    # Replace non-alphanumeric (except single spaces) with spaces
    s = re.sub(r'[^a-z0-9\s]', ' ', s)

    # Collapse multiple spaces into one
    return " ".join(s.split())


def matches_keyword_group(text: str, keyword_group: List[str]) -> bool:
    """
    Checks whether all terms in a keyword group are present in the text,
    respecting token/word boundaries.
    
    Examples:
        - keyword_group=['ar condicionado', '12000'] matches 'Ar Condicionado Split 12.000 BTUs'
        - keyword_group=['9070 xt', 'xfx'] matches 'XFX Radeon RX 9070XT'
        - keyword_group=['pampers', 'xg'] matches 'Fralda Pampers XG', but NOT 'Fralda Pampers XXG'
    """
    norm_text = normalize_text(text)
    if not norm_text:
        return False

    for term in keyword_group:
        norm_term = normalize_text(term)
        if not norm_term:
            continue

        # Split multi-word term into sub-tokens if necessary, or match as whole phrase
        # Using word boundaries \b to prevent partial matches like 'xg' in 'xxg'
        escaped_term = re.escape(norm_term)
        pattern = rf'\b{escaped_term}\b'
        if not re.search(pattern, norm_text):
            return False

    return True


def contains_any_exception(text: str, exceptions: List[str]) -> bool:
    """Checks whether any exception substring/term matches in the text."""
    norm_text = normalize_text(text)
    for exc in exceptions:
        norm_exc = normalize_text(exc)
        if not norm_exc:
            continue
        escaped = re.escape(norm_exc)
        if re.search(rf'\b{escaped}\b', norm_text):
            return True
    return False
