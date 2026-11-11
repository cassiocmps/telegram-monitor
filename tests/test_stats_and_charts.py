import os
from datetime import datetime, timedelta, timezone
import pytest

from src.services.price_parser import (
    parse_numeric_price,
    extract_prices_with_values,
    extract_raw_prices
)
from src.services.stats_service import (
    parse_time_scope,
    calculate_statistics,
    format_stats_report
)
from src.services.chart_service import generate_pricing_chart


def test_parse_numeric_price():
    assert parse_numeric_price("5.199,00") == 5199.0
    assert parse_numeric_price("1.499") == 1499.0
    assert parse_numeric_price("1499,90") == 1499.90
    assert parse_numeric_price("1499.90") == 1499.90
    assert parse_numeric_price("89,90") == 89.90
    assert parse_numeric_price("450") == 450.0
    assert parse_numeric_price("1,299.00") == 1299.0


def test_extract_prices_with_values():
    text = "Placa de Vídeo RTX 4070 por R$ 5.199,00 ou 4.800 reais à vista! Frete grátis."
    results = extract_prices_with_values(text)
    values = [val for _, val in results]
    assert 5199.0 in values
    assert 4800.0 in values


def test_parse_time_scope():
    cutoff, label = parse_time_scope("week")
    assert label == "Last Week"
    assert cutoff is not None
    assert (datetime.now(timezone.utc) - cutoff).days in (6, 7)

    cutoff_month, label_month = parse_time_scope("month")
    assert label_month == "Last Month"
    assert (datetime.now(timezone.utc) - cutoff_month).days in (29, 30)

    cutoff_ever, label_ever = parse_time_scope("ever")
    assert label_ever == "All Time"
    assert cutoff_ever is None


def test_calculate_statistics():
    now = datetime.now(timezone.utc)
    records = [
        {"price": 1000.0, "timestamp": now - timedelta(days=5), "chat_name": "Deals Group", "message_link": ""},
        {"price": 1200.0, "timestamp": now - timedelta(days=3), "chat_name": "Deals Group", "message_link": ""},
        {"price": 1400.0, "timestamp": now - timedelta(days=1), "chat_name": "Promo Chat", "message_link": "http://t.me/1"},
        {"price": 2000.0, "timestamp": now, "chat_name": "Hardware Chat", "message_link": ""},
    ]

    stats = calculate_statistics(records)
    assert stats["count"] == 4
    assert stats["min"] == 1000.0
    assert stats["max"] == 2000.0
    assert stats["mean"] == 1400.0
    assert stats["median"] == 1300.0
    assert stats["cheapest_record"]["price"] == 1000.0

    report = format_stats_report(stats, "RTX 4070", "Last Month")
    assert "RTX 4070" in report
    assert "*Lowest Price (Menor Preço):* R$ 1,000.00" in report
    assert "*Median (Mediana):* R$ 1,300.00" in report
    assert "*Average (Média):* R$ 1,400.00" in report
    assert "Deals Group" in report


def test_generate_pricing_chart(tmp_path):
    now = datetime.now(timezone.utc)
    records = [
        {"price": 3100.0, "timestamp": now - timedelta(days=4), "chat_name": "Deals 1", "message_link": ""},
        {"price": 2950.0, "timestamp": now - timedelta(days=3), "chat_name": "Deals 2", "message_link": ""},
        {"price": 2800.0, "timestamp": now - timedelta(days=2), "chat_name": "Deals 1", "message_link": ""},
        {"price": 3200.0, "timestamp": now - timedelta(days=1), "chat_name": "Deals 3", "message_link": ""},
        {"price": 2750.0, "timestamp": now, "chat_name": "Deals 2", "message_link": ""},
    ]
    stats = calculate_statistics(records)
    out_file = str(tmp_path / "test_chart.png")

    chart_bytes = generate_pricing_chart(
        keyword="RTX 4060",
        scope_label="Last Week",
        records=records,
        stats=stats,
        save_path=out_file
    )

    assert len(chart_bytes) > 1000
    assert chart_bytes[:8] == b"\x89PNG\r\n\x1a\n"  # PNG magic header
    assert os.path.exists(out_file)
