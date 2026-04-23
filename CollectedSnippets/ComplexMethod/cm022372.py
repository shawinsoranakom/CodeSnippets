async def test_light_brightness_property(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_system_nexa_2_device: MagicMock,
) -> None:
    """Test light brightness property conversion."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Find the callback that was registered with the device
    update_callback = find_update_callback(mock_system_nexa_2_device)

    # Test with state = 0.5 (50% in device scale, should be 128 in HA scale)
    await update_callback(StateChange(state=0.5))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 128

    # Test with state = 1.0 (100% in device scale, should be 255 in HA scale)
    await update_callback(StateChange(state=1.0))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 255

    # Test with state = 0.0 (0% - light should be off)
    await update_callback(StateChange(state=0.0))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_OFF

    # Test with state = 0.1 (10% in device scale, should be 26 in HA scale)
    await update_callback(StateChange(state=0.1))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 26