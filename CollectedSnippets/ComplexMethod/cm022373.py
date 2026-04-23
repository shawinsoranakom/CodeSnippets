async def test_coordinator_connection_status(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_system_nexa_2_device: MagicMock,
) -> None:
    """Test coordinator handles connection status updates for light."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Find the callback that was registered with the device
    update_callback = find_update_callback(mock_system_nexa_2_device)

    # Initially, the light should be on (state=0.5 from fixture)
    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON

    # Simulate device disconnection
    await update_callback(ConnectionStatus(connected=False))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Simulate reconnection and state update
    await update_callback(ConnectionStatus(connected=True))
    await update_callback(StateChange(state=0.75))
    await hass.async_block_till_done()

    state = hass.states.get("light.in_wall_dimmer_light")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 191