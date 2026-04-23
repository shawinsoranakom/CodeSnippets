async def test_properties_no_data(
    hass: HomeAssistant,
    load_int: MockConfigEntry,
    mock_client: MagicMock,
    mock_fire_client: SMHIFirePointForecast,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test properties when no API data available."""

    mock_client.async_get_daily_forecast.side_effect = SmhiForecastException("boom")
    freezer.tick(timedelta(minutes=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)

    assert state
    assert state.name == "Test"
    assert state.state == STATE_UNAVAILABLE
    assert state.attributes[ATTR_ATTRIBUTION] == "Swedish weather institute (SMHI)"

    mock_client.async_get_daily_forecast.side_effect = None
    mock_client.async_get_daily_forecast.return_value = None
    freezer.tick(timedelta(minutes=35))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)

    assert state
    assert state.name == "Test"
    assert state.state == "cloudy"
    assert ATTR_SMHI_THUNDER_PROBABILITY not in state.attributes
    assert state.attributes[ATTR_ATTRIBUTION] == "Swedish weather institute (SMHI)"