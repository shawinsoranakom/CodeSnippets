async def test_gauge_icon() -> None:
    """Test icon generator for gauge sensor."""

    GAUGE_EMPTY = "mdi:gauge-empty"
    GAUGE_LOW = "mdi:gauge-low"
    GAUGE = "mdi:gauge"
    GAUGE_FULL = "mdi:gauge-full"

    assert icon_for_gauge_level(None) == GAUGE_EMPTY
    assert icon_for_gauge_level(0) == GAUGE_EMPTY
    assert icon_for_gauge_level(5) == GAUGE_LOW
    assert icon_for_gauge_level(40) == GAUGE
    assert icon_for_gauge_level(80) == GAUGE_FULL
    assert icon_for_gauge_level(100) == GAUGE_FULL

    assert icon_for_gauge_level(None, 10) == GAUGE_EMPTY
    assert icon_for_gauge_level(0, 10) == GAUGE_EMPTY
    assert icon_for_gauge_level(5, 10) == GAUGE_EMPTY
    assert icon_for_gauge_level(40, 10) == GAUGE_LOW
    assert icon_for_gauge_level(80, 10) == GAUGE
    assert icon_for_gauge_level(100, 10) == GAUGE_FULL