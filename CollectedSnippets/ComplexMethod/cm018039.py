async def test_config_defaults() -> None:
    """Test config defaults."""
    hass = Mock()
    hass.data = {}
    config = Config(hass, "/test/ha-config")
    assert config.hass is hass
    assert config.latitude == 0
    assert config.longitude == 0
    assert config.elevation == 0
    assert config.location_name == "Home"
    assert config.time_zone == "UTC"
    assert config.internal_url is None
    assert config.external_url is None
    assert config.config_source is ConfigSource.DEFAULT
    assert config.skip_pip is False
    assert config.skip_pip_packages == []
    assert config.components == set()
    assert config.api is None
    assert config.config_dir == "/test/ha-config"
    assert config.allowlist_external_dirs == set()
    assert config.allowlist_external_urls == set()
    assert config.media_dirs == {}
    assert config.recovery_mode is False
    assert config.legacy_templates is False
    assert config.currency == "EUR"
    assert config.country is None
    assert config.language == "en"
    assert config.radius == 100