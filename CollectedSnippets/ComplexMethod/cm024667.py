async def test_verify_throttle(
    hass: HomeAssistant,
    mock_nextbus: MagicMock,
    mock_nextbus_lists: MagicMock,
    mock_nextbus_predictions: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Verify that the sensor coordinator is throttled correctly."""

    # Set rate limit past threshold, should be ignored for first request
    mock_client = mock_nextbus.return_value
    mock_client.rate_limit_percent = 99.0
    mock_client.rate_limit_reset = datetime.now() + timedelta(seconds=30)

    # Do a request with the initial config and get predictions
    await assert_setup_sensor(hass, CONFIG_BASIC)

    # Validate the predictions are present
    state = hass.states.get(SENSOR_ID)
    assert state is not None
    assert state.state == "2019-03-28T21:09:31+00:00"
    assert state.attributes["agency"] == VALID_AGENCY
    assert state.attributes["route"] == VALID_ROUTE_TITLE
    assert state.attributes["stop"] == VALID_STOP_TITLE
    assert state.attributes["upcoming"] == "1, 2, 3, 10"

    # Update the predictions mock to return a different result
    mock_nextbus_predictions.return_value = NO_UPCOMING

    # Move time forward and bump the rate limit reset time
    mock_client.rate_limit_reset = freezer.tick(31) + timedelta(seconds=30)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify that the sensor state is unchanged
    state = hass.states.get(SENSOR_ID)
    assert state is not None
    assert state.state == "2019-03-28T21:09:31+00:00"

    # Move time forward past the rate limit reset time
    freezer.tick(31)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    # Verify that the sensor state is updated with the new predictions
    state = hass.states.get(SENSOR_ID)
    assert state is not None
    assert state.attributes["upcoming"] == "No upcoming predictions"
    assert state.state == "unknown"