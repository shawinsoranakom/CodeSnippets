async def test_update_available(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_federwiege: MagicMock,
) -> None:
    """Test smarla update initial state and behavior when an update gets available."""
    assert await setup_integration(hass, mock_config_entry)

    state = hass.states.get(UPDATE_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "1.0.0"
    assert state.attributes[ATTR_LATEST_VERSION] == "1.0.0"

    mock_federwiege.check_firmware_update.return_value = ("1.1.0", "")
    await async_update_entity(hass, UPDATE_ENTITY_ID)
    await hass.async_block_till_done()

    state = hass.states.get(UPDATE_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_LATEST_VERSION] == "1.1.0"