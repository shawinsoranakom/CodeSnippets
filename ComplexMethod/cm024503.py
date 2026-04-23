async def test_create_lock_with_linked_keypad(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test creation of a lock with a linked keypad that both have a battery."""
    lock_one = await _mock_lock_from_fixture(hass, "get_lock.doorsense_init.json")
    await _create_yale_with_devices(hass, [lock_one])

    battery_state = hass.states.get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert battery_state.state == "88"
    assert battery_state.attributes["unit_of_measurement"] == PERCENTAGE

    entry = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert entry
    assert entry.unique_id == "A6697750D607098BAE8D6BAA11EF8063_device_battery"

    keypad_battery_state = hass.states.get("sensor.front_door_lock_keypad_battery")
    assert keypad_battery_state.state == "62"
    assert keypad_battery_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    entry = entity_registry.async_get("sensor.front_door_lock_keypad_battery")
    assert entry
    assert entry.unique_id == "5bc65c24e6ef2a263e1450a8_linked_keypad_battery"