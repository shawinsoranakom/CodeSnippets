async def test_load_unload(
    hass: HomeAssistant,
    door_sensor: Sensor,
    transport: MagicMock,
    integration: MockConfigEntry,
    receive_message: Callable[[str], None],
) -> None:
    """Test loading and unloading the MySensors config entry."""
    config_entry = integration

    assert config_entry.state is ConfigEntryState.LOADED

    entity_id = "binary_sensor.door_sensor_1_1"
    state = hass.states.get(entity_id)

    assert state
    assert state.state != STATE_UNAVAILABLE

    receive_message("1;1;1;0;16;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state != STATE_UNAVAILABLE

    assert await hass.config_entries.async_unload(config_entry.entry_id)

    assert transport.return_value.disconnect.call_count == 1

    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_UNAVAILABLE

    receive_message("1;1;1;0;16;1\n")
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state
    assert state.state == STATE_UNAVAILABLE