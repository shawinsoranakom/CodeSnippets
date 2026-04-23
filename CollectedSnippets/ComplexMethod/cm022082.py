async def test_climate_local(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_local_config_entry: MockConfigEntry,
    mock_adax_local: AsyncMock,
) -> None:
    """Test states of the (local) Climate entity."""
    await setup_integration(hass, mock_local_config_entry)
    mock_adax_local.get_status.assert_called_once()

    assert len(hass.states.async_entity_ids(Platform.CLIMATE)) == 1
    entity_id = hass.states.async_entity_ids(Platform.CLIMATE)[0]

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 20
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 15

    mock_adax_local.get_status.side_effect = Exception()
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE