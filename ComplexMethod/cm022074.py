async def test_ev_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_ituran: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test sensor is marked as unavailable when we can't reach the Ituran service."""
    entities = [
        "binary_sensor.mock_model_charging",
    ]

    await setup_integration(hass, mock_config_entry)

    for entity_id in entities:
        state = hass.states.get(entity_id)
        assert state
        assert state.state != STATE_UNAVAILABLE

    mock_ituran.get_vehicles.side_effect = IturanApiError
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for entity_id in entities:
        state = hass.states.get(entity_id)
        assert state
        assert state.state == STATE_UNAVAILABLE

    mock_ituran.get_vehicles.side_effect = None
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    for entity_id in entities:
        state = hass.states.get(entity_id)
        assert state
        assert state.state != STATE_UNAVAILABLE