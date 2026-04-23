async def test_imperial_deprecated_log_warning(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test deprecated imperial unit system logs warning."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Home",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "currency": "USD",
            "country": "US",
            "language": "en",
            "radius": 150,
        },
    )

    assert hass.config.latitude == 60
    assert hass.config.longitude == 50
    assert hass.config.elevation == 25
    assert hass.config.location_name == "Home"
    assert hass.config.units is US_CUSTOMARY_SYSTEM
    assert hass.config.time_zone == "America/New_York"
    assert hass.config.currency == "USD"
    assert hass.config.country == "US"
    assert hass.config.language == "en"
    assert hass.config.radius == 150