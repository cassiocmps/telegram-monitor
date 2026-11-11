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


def sanitize_text_for_prices(text: str) -> str:
    """
    Strips out unit-price indicators and installment noise to prevent
    distorting total product pricing.
    
    Examples filtered:
        - '(R$ 6,60 cada pacotinho)'
        - '(1,24 por unidade)'
        - 'R$ 0,85 cada fralda'
        - '12x de R$ 350,00' (when cash price exists)
    """
    # 1. Remove parenthetical unit prices, e.g. '(R$ 6,60 cada pacotinho)', '(1,24 por unidade)'
    cleaned = re.sub(
        r'\([^)]*?(?:cada|por|a)\s+(?:unidade|pacotinho|pct|fralda|tira|lata|unid|dose|capsula)[^)]*?\)',
        ' ',
        text,
        flags=re.IGNORECASE
    )

    # 2. Remove inline unit price mentions e.g. 'R$ 6,60 cada pacotinho'
    cleaned = re.sub(
        r'(?:r\$|\$)?\s*\d+[.,]?\d*\s*(?:cada|por|a)\s+(?:unidade|pacotinho|pct|fralda|tira|lata|unid|dose|capsula)\b',
        ' ',
        cleaned,
        flags=re.IGNORECASE
    )

    # 3. Mask installment amounts (e.g. '12x de R$ 350,00' or '10x R$ 250')
    # but only if there is also an upfront/total price in the text
    has_total_price = bool(re.search(r'(?:por|a vista|à vista|no pix|total|oferta)[^.\n]*?(?:r\$|\$)\s*(\d+)', text, re.IGNORECASE))
    if has_total_price or re.search(r'(?:r\$|\$)\s*\d+[^.\n]*?(?:12x|10x|\dx)', text, re.IGNORECASE):
        cleaned = re.sub(
            r'\b\d{1,2}\s*x\s*(?:de\s*)?(?:r\$|\$)?\s*\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?',
            ' ',
            cleaned,
            flags=re.IGNORECASE
        )

    # 4. Mask coupon/discount amounts e.g. 'R$ 30 OFF', 'R$ 50 de desconto', 'cupom de R$ 20'
    cleaned = re.sub(
        r'(?:cupom\s+de\s+)?(?:r\$|\$)\s*\d+[.,]?\d*\s*(?:off|de\s+desconto)\b',
        ' ',
        cleaned,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r'\b(?:cupom|desconto)\s+de\s+(?:r\$|\$)?\s*\d+[.,]?\d*\b',
        ' ',
        cleaned,
        flags=re.IGNORECASE
    )

    return cleaned


def extract_prices_with_values(text: str) -> List[Tuple[str, float]]:
    """
    Extracts price mentions from text and returns a list of tuples:
    [(raw_representation, float_value), ...]
    """
    results: List[Tuple[str, float]] = []
    seen_values = set()

    sanitized = sanitize_text_for_prices(text)

    # Pattern 1: Prefixed with R$, $, BRL, US$
    prefix_pattern = r'(?:r\$|\$|brl|us\$)\s*(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?|\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?)'
    for match in re.finditer(prefix_pattern, sanitized, flags=re.IGNORECASE):
        raw_val = match.group(1)
        numeric_val = parse_numeric_price(raw_val)
        if numeric_val is not None and numeric_val not in seen_values:
            if 0.5 <= numeric_val <= 10_000_000:
                seen_values.add(numeric_val)
                results.append((raw_val, numeric_val))

    # Pattern 2: Suffix with 'reais' e.g. '1.499 reais' or '150 reais'
    suffix_pattern = r'(\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?|\d+(?:[.,]\d{1,2})?)\s*(?:reais\b)'
    for match in re.finditer(suffix_pattern, sanitized, flags=re.IGNORECASE):
        raw_val = match.group(1)
        numeric_val = parse_numeric_price(raw_val)
        if numeric_val is not None and numeric_val not in seen_values:
            if 0.5 <= numeric_val <= 10_000_000:
                seen_values.add(numeric_val)
                results.append((raw_val, numeric_val))

    # Fallback to unsanitized text if nothing was found (ensures we don't miss isolated prices)
    if not results:
        for match in re.finditer(prefix_pattern, text, flags=re.IGNORECASE):
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
