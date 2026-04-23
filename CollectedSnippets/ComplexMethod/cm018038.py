async def test_loading_configuration(hass: HomeAssistant) -> None:
    """Test loading core config onto hass object."""
    await async_process_ha_core_config(
        hass,
        {
            "latitude": 60,
            "longitude": 50,
            "elevation": 25,
            "name": "Huis",
            "unit_system": "imperial",
            "time_zone": "America/New_York",
            "allowlist_external_dirs": "/etc",
            "external_url": "https://www.example.com",
            "internal_url": "http://example.local",
            "media_dirs": {"mymedia": "/usr"},
            "debug": True,
            "currency": "EUR",
            "country": "SE",
            "language": "sv",
            "radius": 150,
            "webrtc": {"ice_servers": [{"url": "stun:custom_stun_server:3478"}]},
        },
    )

    assert hass.config.latitude == 60
    assert hass.config.longitude == 50
    assert hass.config.elevation == 25
    assert hass.config.location_name == "Huis"
    assert hass.config.units is US_CUSTOMARY_SYSTEM
    assert hass.config.time_zone == "America/New_York"
    assert hass.config.external_url == "https://www.example.com"
    assert hass.config.internal_url == "http://example.local"
    assert len(hass.config.allowlist_external_dirs) == 3
    assert "/etc" in hass.config.allowlist_external_dirs
    assert "/usr" in hass.config.allowlist_external_dirs
    assert hass.config.media_dirs == {"mymedia": "/usr"}
    assert hass.config.config_source is ConfigSource.YAML
    assert hass.config.debug is True
    assert hass.config.currency == "EUR"
    assert hass.config.country == "SE"
    assert hass.config.language == "sv"
    assert hass.config.radius == 150
    assert hass.config.webrtc == RTCConfiguration(
        [RTCIceServer(urls=["stun:custom_stun_server:3478"])]
    )