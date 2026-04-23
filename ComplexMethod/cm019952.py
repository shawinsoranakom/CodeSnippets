async def test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_brother_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Ensure that we mark the entities unavailable correctly when device is offline."""
    entity_id = "sensor.hl_l2340dw_status"
    await init_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "waiting"

    mock_brother_client.async_update.side_effect = ConnectionError
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_brother_client.async_update.side_effect = None
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "waiting"