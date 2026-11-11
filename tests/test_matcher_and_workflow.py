import os
import json
import pytest

from src.services.text_matcher import (
    normalize_text,
    matches_keyword_group,
    contains_any_exception
)
from src.services.price_parser import extract_prices_with_values
from src.services.dedup_service import AlertDeduplicator
from src.services.keyword_service import (
    load_keywords,
    save_keywords,
    add_keyword_group,
    delete_keyword_group
)


def test_normalize_text_numbers_and_units():
    # Number thousand dots
    assert "12000" in normalize_text("12.000")
    assert "12000" in normalize_text("12000")
    assert "1499" in normalize_text("1.499")

    # Alphanumeric transition
    norm_btu = normalize_text("12.000BTUs")
    assert "12000" in norm_btu
    assert "btus" in norm_btu

    norm_gpu = normalize_text("RX 9070XT")
    assert "9070 xt" in norm_gpu


def test_ar_condicionado_12000_matching():
    kw_group = ["ar condicionado", "12000"]

    # Should match variations with dots, hyphens, and units
    assert matches_keyword_group("Ar Condicionado Split 12.000 BTUs Inverter", kw_group)
    assert matches_keyword_group("Ar-Condicionado 12000 BTUs", kw_group)
    assert matches_keyword_group("ar condicionado 12000btu", kw_group)
    assert matches_keyword_group("AR CONDICIONADO 12.000", kw_group)
    assert matches_keyword_group("Oferta: Ar Condicionado Inverter 12.000 Frio", kw_group)

    # Should NOT match different capacity or different product
    assert not matches_keyword_group("Ar Condicionado Split 9.000 BTUs", kw_group)
    assert not matches_keyword_group("Ar Condicionado Split 18.000 BTUs", kw_group)
    assert not matches_keyword_group("Ventilador 12000 RPM", kw_group)


def test_gpu_and_size_boundary_matching():
    # 9070 XT variations
    gpu_group = ["9070 xt", "xfx"]
    assert matches_keyword_group("Placa XFX Radeon RX 9070XT Triple Fan", gpu_group)
    assert matches_keyword_group("XFX RX 9070 XT 16GB", gpu_group)
    assert matches_keyword_group("XFX RX-9070-XT", gpu_group)

    # Size XG vs XXG
    size_group = ["pampers", "ajuste total", "xg"]
    assert matches_keyword_group("Fralda Pampers Pants Ajuste Total XG com 82", size_group)
    assert matches_keyword_group("Fralda Pampers Ajuste Total (XG)", size_group)
    # Strictly must NOT match XXG or XXXG
    assert not matches_keyword_group("Fralda Pampers Pants Ajuste Total XXG com 120 Unidades", size_group)
    assert not matches_keyword_group("Fralda Pampers Pants Ajuste Total XXXG", size_group)


def test_unit_price_and_coupon_filtering():
    # Pack price with unit price in parentheses
    text1 = "Lenços Umedecidos Pampers Aroma de Aloe Vera 192 Unidades Por: R$ 26,39 (R$ 6,60 cada pacotinho)"
    extracted1 = extract_prices_with_values(text1)
    values1 = [p[1] for p in extracted1]
    assert 26.39 in values1
    assert 6.60 not in values1

    # Diaper box with unit price
    text2 = "Fralda Pampers Pants Ajuste Total XG com 82 Por: R$ 85,50 à vista (1,04 por unidade)"
    extracted2 = extract_prices_with_values(text2)
    values2 = [p[1] for p in extracted2]
    assert 85.50 in values2
    assert 1.04 not in values2

    # Coupon discount mask
    text3 = "Ar Condicionado 12.000 BTUs Por: R$ 1.699 no pix com cupom de R$ 100 OFF"
    extracted3 = extract_prices_with_values(text3)
    values3 = [p[1] for p in extracted3]
    assert 1699.0 in values3
    assert 100.0 not in values3


def test_deduplicator():
    dedup = AlertDeduplicator(cooldown_seconds=300)
    links = ["https://www.pichau.com.br/item-123"]
    prices = [2999.0]
    kw = ["9070 xt", "xfx"]

    key1 = dedup.generate_deal_key(kw, links, prices, "Pichau Promo")
    assert not dedup.is_duplicate(key1)

    # Second check within cooldown must be detected as duplicate
    assert dedup.is_duplicate(key1)

    # Different product link must not be blocked
    key2 = dedup.generate_deal_key(kw, ["https://www.pichau.com.br/item-456"], prices, "Pichau Promo 2")
    assert not dedup.is_duplicate(key2)


def test_keyword_service(tmp_path):
    test_file = str(tmp_path / "test_keywords.json")
    import src.services.keyword_service as ks
    original_path = ks.KEYWORDS_FILE
    try:
        ks.KEYWORDS_FILE = test_file
        assert ks.save_keywords([["ar condicionado", "12000"], ["rtx 4070"]])
        loaded = ks.load_keywords()
        assert len(loaded) == 2
        assert loaded[0] == ["ar condicionado", "12000"]

        assert ks.add_keyword_group(["rx 9070 xt", "xfx"])
        assert len(ks.load_keywords()) == 3

        assert ks.delete_keyword_group(1)
        assert len(ks.load_keywords()) == 2
    finally:
        ks.KEYWORDS_FILE = original_path
