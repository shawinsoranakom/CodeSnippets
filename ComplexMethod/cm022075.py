async def __test_availability(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_ituran: AsyncMock,
    mock_config_entry: MockConfigEntry,
    ev_entity_names: list[str] | None = None,
) -> None:
    entities = [
        "sensor.mock_model_address",
        "sensor.mock_model_battery_voltage",
        "sensor.mock_model_heading",
        "sensor.mock_model_last_update_from_vehicle",
        "sensor.mock_model_mileage",
        "sensor.mock_model_speed",
        *(ev_entity_names if ev_entity_names is not None else []),
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