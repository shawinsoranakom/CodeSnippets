async def test_entity_availability(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_federwiege: MagicMock,
) -> None:
    """Test entity state when device becomes unavailable/available."""
    assert await setup_integration(hass, mock_config_entry)

    # Initially available
    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE

    # Simulate device becoming unavailable
    mock_federwiege.available = False
    await update_property_listeners(mock_federwiege)
    await hass.async_block_till_done()

    # Verify state reflects unavailable
    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Simulate device becoming available again
    mock_federwiege.available = True
    await update_property_listeners(mock_federwiege)
    await hass.async_block_till_done()

    # Verify state reflects available again
    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE