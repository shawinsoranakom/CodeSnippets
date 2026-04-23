async def test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_imgw_pib_client: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Ensure that we mark the entities unavailable correctly when service is offline."""
    await init_integration(hass, mock_config_entry)

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "526.0"

    mock_imgw_pib_client.get_hydrological_data.side_effect = ApiError("API Error")
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_UNAVAILABLE

    mock_imgw_pib_client.get_hydrological_data.side_effect = None
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state != STATE_UNAVAILABLE
    assert state.state == "526.0"