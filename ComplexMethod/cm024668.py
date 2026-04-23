async def test_unload_entry(
    hass: HomeAssistant,
    mock_nextbus: MagicMock,
    mock_nextbus_lists: MagicMock,
    mock_nextbus_predictions: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that the sensor can be unloaded."""
    config_entry1 = await assert_setup_sensor(hass, CONFIG_BASIC)
    await assert_setup_sensor(hass, CONFIG_BASIC_2, route_title=ROUTE_TITLE_2)

    # Verify the first sensor
    state = hass.states.get(SENSOR_ID)
    assert state is not None
    assert state.state == "2019-03-28T21:09:31+00:00"
    assert state.attributes["agency"] == VALID_AGENCY
    assert state.attributes["route"] == VALID_ROUTE_TITLE
    assert state.attributes["stop"] == VALID_STOP_TITLE
    assert state.attributes["upcoming"] == "1, 2, 3, 10"

    # Verify the second sensor
    state = hass.states.get(SENSOR_ID_2)
    assert state is not None
    assert state.state == "2019-03-28T21:09:39+00:00"
    assert state.attributes["agency"] == VALID_AGENCY
    assert state.attributes["route"] == ROUTE_TITLE_2
    assert state.attributes["stop"] == VALID_STOP_TITLE
    assert state.attributes["upcoming"] == "90"

    # Update mock to return new predictions
    new_predictions = deepcopy(BASIC_RESULTS)
    new_predictions[1]["values"] = [{"minutes": 5, "timestamp": 1553807375000}]
    mock_nextbus_predictions.return_value = new_predictions

    # Unload config entry 1
    await hass.config_entries.async_unload(config_entry1.entry_id)
    await hass.async_block_till_done()
    assert config_entry1.state is ConfigEntryState.NOT_LOADED

    # Skip ahead in time
    freezer.tick(120)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Check update for new predictions
    state = hass.states.get(SENSOR_ID_2)
    assert state is not None
    assert state.attributes["upcoming"] == "5"
    assert state.state == "2019-03-28T21:09:35+00:00"