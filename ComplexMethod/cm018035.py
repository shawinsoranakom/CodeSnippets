async def test_loading_configuration_from_storage(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test loading core config onto hass object."""
    hass_storage["core.config"] = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "metric",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "currency": "EUR",
            "country": "SE",
            "language": "sv",
            "radius": 150,
        },
        "key": "core.config",
        "version": 1,
        "minor_version": 4,
    }
    await async_process_ha_core_config(hass, {"allowlist_external_dirs": "/etc"})

    assert hass.config.latitude == 55
    assert hass.config.longitude == 13
    assert hass.config.elevation == 10
    assert hass.config.location_name == "Home"
    assert hass.config.units is METRIC_SYSTEM
    assert hass.config.time_zone == "Europe/Copenhagen"
    assert hass.config.external_url == "https://www.example.com"
    assert hass.config.internal_url == "http://example.local"
    assert hass.config.currency == "EUR"
    assert hass.config.country == "SE"
    assert hass.config.language == "sv"
    assert hass.config.radius == 150
    assert len(hass.config.allowlist_external_dirs) == 3
    assert "/etc" in hass.config.allowlist_external_dirs
    assert hass.config.config_source is ConfigSource.STORAGE