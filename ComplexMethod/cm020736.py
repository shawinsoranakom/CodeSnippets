async def test_create_lock_with_low_battery_linked_keypad(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test creation of a lock with a linked keypad that both have a battery."""
    lock_one = await _mock_lock_from_fixture(hass, "get_lock.low_keypad_battery.json")
    await _create_august_with_devices(hass, [lock_one])
    states = hass.states

    battery_state = states.get("sensor.a6697750d607098bae8d6baa11ef8063_name_battery")
    assert battery_state.state == "88"
    assert battery_state.attributes["unit_of_measurement"] == PERCENTAGE
    entry = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_battery"
    )
    assert entry
    assert entry.unique_id == "A6697750D607098BAE8D6BAA11EF8063_device_battery"

    keypad_battery_state = states.get("sensor.front_door_lock_keypad_battery")
    assert keypad_battery_state.state == "10"
    assert keypad_battery_state.attributes[ATTR_UNIT_OF_MEASUREMENT] == PERCENTAGE
    entry = entity_registry.async_get("sensor.front_door_lock_keypad_battery")
    assert entry
    assert entry.unique_id == "5bc65c24e6ef2a263e1450a8_linked_keypad_battery"

    # No activity means it will be unavailable until someone unlocks/locks it
    operator_entry = entity_registry.async_get(
        "sensor.a6697750d607098bae8d6baa11ef8063_name_operator"
    )
    assert operator_entry.unique_id == "A6697750D607098BAE8D6BAA11EF8063_lock_operator"

    operator_state = states.get("sensor.a6697750d607098bae8d6baa11ef8063_name_operator")
    assert operator_state.state == STATE_UNKNOWN