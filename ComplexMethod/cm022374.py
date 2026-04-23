async def test_coordinator_state_change(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_system_nexa_2_device: MagicMock,
) -> None:
    """Test coordinator handles state change updates for light."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Find the callback that was registered with the device
    update_callback = find_update_callback(mock_system_nexa_2_device)

    # Change state to off (0.0)
    await update_callback(StateChange(state=0.0))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_OFF

    # Change state to 25% (0.25)
    await update_callback(StateChange(state=0.25))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 64  # 0.25 * 255 ≈ 64

    # Change state to full brightness (1.0)
    await update_callback(StateChange(state=1.0))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 255