async def test_device_battery_level(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    entity_registry: er.EntityRegistry,
) -> None:
    """Test battery level sensor for devices."""

    assert await integration_setup()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    state = hass.states.get("sensor.charge_2_battery_level")
    assert state
    assert state.state == "60"
    assert state.attributes == {
        "attribution": "Data provided by Fitbit.com",
        "friendly_name": "Charge 2 Battery level",
        "device_class": "battery",
        "unit_of_measurement": "%",
    }

    state = hass.states.get("sensor.aria_air_battery_level")
    assert state
    assert state.state == "95"
    assert state.attributes == {
        "attribution": "Data provided by Fitbit.com",
        "friendly_name": "Aria Air Battery level",
        "device_class": "battery",
        "unit_of_measurement": "%",
    }