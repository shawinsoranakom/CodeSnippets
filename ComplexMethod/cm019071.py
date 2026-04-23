async def test_temperature_range(
    hass: HomeAssistant,
    mock_huum_client: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the temperature range."""
    # API response.
    state = hass.states.get(ENTITY_ID)
    assert state.attributes["min_temp"] == 40
    assert state.attributes["max_temp"] == 110

    # Empty/unconfigured API response should return default values.
    mock_huum_client.status.return_value.sauna_config.min_temp = 0
    mock_huum_client.status.return_value.sauna_config.max_temp = 0

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["min_temp"] == CONFIG_DEFAULT_MIN_TEMP
    assert state.attributes["max_temp"] == CONFIG_DEFAULT_MAX_TEMP

    # No sauna config should return default values.
    mock_huum_client.status.return_value.sauna_config = None

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["min_temp"] == CONFIG_DEFAULT_MIN_TEMP
    assert state.attributes["max_temp"] == CONFIG_DEFAULT_MAX_TEMP

    # Custom configured API response.
    mock_huum_client.status.return_value.sauna_config = SaunaConfig(
        child_lock="OFF",
        max_heating_time=3,
        min_heating_time=0,
        max_temp=80,
        min_temp=50,
        max_timer=0,
        min_timer=0,
    )

    freezer.tick(timedelta(seconds=30))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    assert state.attributes["min_temp"] == 50
    assert state.attributes["max_temp"] == 80