async def test_loading_configuration_from_storage_with_yaml_only(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test loading core and YAML config onto hass object."""
    hass_storage["core.config"] = {
        "data": {
            "elevation": 10,
            "latitude": 55,
            "location_name": "Home",
            "longitude": 13,
            "time_zone": "Europe/Copenhagen",
            "unit_system": "metric",
        },
        "key": "core.config",
        "version": 1,
    }
    await async_process_ha_core_config(
        hass, {"media_dirs": {"mymedia": "/usr"}, "allowlist_external_dirs": "/etc"}
    )

    assert hass.config.latitude == 55
    assert hass.config.longitude == 13
    assert hass.config.elevation == 10
    assert hass.config.location_name == "Home"
    assert hass.config.units is METRIC_SYSTEM
    assert hass.config.time_zone == "Europe/Copenhagen"
    assert len(hass.config.allowlist_external_dirs) == 3
    assert "/etc" in hass.config.allowlist_external_dirs
    assert hass.config.media_dirs == {"mymedia": "/usr"}
    assert hass.config.config_source is ConfigSource.STORAGE