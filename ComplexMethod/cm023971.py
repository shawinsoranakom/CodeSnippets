async def test_device_battery(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    entity_registry: er.EntityRegistry,
) -> None:
    """Test battery level sensor for devices."""

    assert await integration_setup()
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    state = hass.states.get("sensor.charge_2_battery")
    assert state
    assert state.state == "Medium"
    assert state.attributes == {
        "attribution": "Data provided by Fitbit.com",
        "friendly_name": "Charge 2 Battery",
        "icon": "mdi:battery-50",
        "model": "Charge 2",
        "type": "tracker",
    }

    entry = entity_registry.async_get("sensor.charge_2_battery")
    assert entry
    assert entry.unique_id == f"{PROFILE_USER_ID}_devices/battery_816713257"

    state = hass.states.get("sensor.aria_air_battery")
    assert state
    assert state.state == "High"
    assert state.attributes == {
        "attribution": "Data provided by Fitbit.com",
        "friendly_name": "Aria Air Battery",
        "icon": "mdi:battery",
        "model": "Aria Air",
        "type": "scale",
    }

    entry = entity_registry.async_get("sensor.aria_air_battery")
    assert entry
    assert entry.unique_id == f"{PROFILE_USER_ID}_devices/battery_016713257"