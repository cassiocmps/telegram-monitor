import re
from typing import List, Tuple, Optional


def parse_numeric_price(raw_val: str) -> Optional[float]:
    """
    Parses a raw price string into a float, taking into account
    Brazilian and international currency formats.

    Examples:
        '5.199,00' -> 5199.0
        '1.499'    -> 1499.0
        '1499,90'  -> 1499.90
        '1499.90'  -> 1499.90
        '89,90'    -> 89.90
        '450'      -> 450.0
    """
    cleaned = raw_val.strip()
    if not cleaned:
        return None

    # Case 1: contains both '.' and ','
    if "." in cleaned and "," in cleaned:
        dot_idx = cleaned.rfind(".")
        comma_idx = cleaned.rfind(",")
        if dot_idx < comma_idx:
            # Brazilian format: 1.299,90 -> 1299.90
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US format: 1,299.90 -> 1299.90
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        # e.g., '1499,90' or '89,90' -> decimal comma
        cleaned = cleaned.replace(",", ".")
    elif "." in cleaned:
        # e.g., '1.499' (thousand separator) vs '1499.99' (decimal dot)
        parts = cleaned.split(".")
        if len(parts) > 2:
            # e.g. 1.234.567 -> thousand dots
            cleaned = "".join(parts)
        elif len(parts) == 2:
            integer_part, dec_part = parts
            # In Brazilian context, exactly 3 digits after a single dot (e.g. 1.499, 5.000)
            # is almost always a thousand separator, unless it's fractional cents
            if len(dec_part) == 3 and len(integer_part) <= 3:
                cleaned = f"{integer_part}{dec_part}"
            else:
                cleaned = f"{integer_part}.{dec_part}"

    try:
        val = float(cleaned)
        # Avoid nonsensical zero or negative prices
        return val if val > 0 else None
    except ValueError:
        return None


def extract_prices_with_values(text: str) -> List[Tuple[str, float]]:
    """
    Extracts price mentions from text and returns a list of tuples:
    [(raw_representation, float_value), ...]
    """
    results: List[Tuple[str, float]] = []
    seen_values = set()

    # Pattern 1: Prefixed with R$, $, BRL, US$
    prefix_pattern = r'(?:r\$|\$|brl|us\$)\s*(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)'
    for match in re.finditer(prefix_pattern, text, flags=re.IGNORECASE):
        raw_val = match.group(1)
        numeric_val = parse_numeric_price(raw_val)
        if numeric_val is not None and numeric_val not in seen_values:
            # Filter out unrealistic thresholds (e.g. less than 1 or over 10 million)
            if 0.5 <= numeric_val <= 10_000_000:
                seen_values.add(numeric_val)
                results.append((raw_val, numeric_val))

    # Pattern 2: Suffix with 'reais' e.g. '1.499 reais' or '150 reais'
    suffix_pattern = r'(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(?:reais\b)'
    for match in re.finditer(suffix_pattern, text, flags=re.IGNORECASE):
        raw_val = match.group(1)
        numeric_val = parse_numeric_price(raw_val)
        if numeric_val is not None and numeric_val not in seen_values:
            if 0.5 <= numeric_val <= 10_000_000:
                seen_values.add(numeric_val)
                results.append((raw_val, numeric_val))

    return results


def extract_raw_prices(text: str) -> List[str]:
    """Helper to return just the string representations of extracted prices."""
    pairs = extract_prices_with_values(text)
    return [p[0] for p in pairs]
