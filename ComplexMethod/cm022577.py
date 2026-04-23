async def test_update_errors(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test errors during updates."""
    await setup_uptimerobot_integration(hass)

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        side_effect=UptimeRobotException,
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
        assert entity.state == STATE_UNAVAILABLE

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        return_value=mock_uptimerobot_api_response(data=[MOCK_UPTIMEROBOT_MONITOR]),
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
        assert entity.state == STATE_ON

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        side_effect=Exception("Unexpected error"),
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
        assert entity.state == STATE_UNAVAILABLE

    assert "Error fetching uptimerobot data:" in caplog.text