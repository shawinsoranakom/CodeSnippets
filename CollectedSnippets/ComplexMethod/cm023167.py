async def test_notification_off_state(
    hass: HomeAssistant,
    lock_popp_electric_strike_lock_control: Node,
) -> None:
    """Test the description off_state attribute of certain notification sensors."""
    node = lock_popp_electric_strike_lock_control
    # Remove all other values except the door state value.
    node.values = {
        value_id: value
        for value_id, value in node.values.items()
        if value_id == "62-113-0-Access Control-Door state"
    }

    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    door_states = [
        state
        for state in hass.states.async_all("binary_sensor")
        if state.attributes.get(ATTR_DEVICE_CLASS) == BinarySensorDeviceClass.DOOR
    ]

    # Only one entity should be created for the Door state notification states.
    assert len(door_states) == 1

    state = door_states[0]
    assert state
    assert state.entity_id == "binary_sensor.node_62_window_door_is_open"