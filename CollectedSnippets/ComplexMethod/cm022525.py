async def test_setting_location(hass: HomeAssistant) -> None:
    """Test setting the location."""
    await async_setup_component(hass, "homeassistant", {})
    events = async_capture_events(hass, EVENT_CORE_CONFIG_UPDATE)
    # Just to make sure that we are updating values.
    assert hass.config.latitude != 30
    assert hass.config.longitude != 40
    elevation = hass.config.elevation
    assert elevation != 50
    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40},
        blocking=True,
    )
    assert len(events) == 1
    assert hass.config.latitude == 30
    assert hass.config.longitude == 40
    assert hass.config.elevation == elevation

    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40, "elevation": 50},
        blocking=True,
    )
    assert hass.config.latitude == 30
    assert hass.config.longitude == 40
    assert hass.config.elevation == 50

    await hass.services.async_call(
        "homeassistant",
        SERVICE_SET_LOCATION,
        {"latitude": 30, "longitude": 40, "elevation": 0},
        blocking=True,
    )
    assert hass.config.latitude == 30
    assert hass.config.longitude == 40
    assert hass.config.elevation == 0