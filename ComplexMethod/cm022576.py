async def test_reauthentication_trigger_after_setup(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test reauthentication trigger."""
    mock_config_entry = await setup_uptimerobot_integration(hass)

    assert (binary_sensor := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert binary_sensor.state == STATE_ON

    with patch(
        "pyuptimerobot.UptimeRobot.async_get_monitors",
        side_effect=UptimeRobotAuthenticationException,
    ):
        freezer.tick(COORDINATOR_UPDATE_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert (entity := hass.states.get(UPTIMEROBOT_BINARY_SENSOR_TEST_ENTITY))
    assert entity.state == STATE_UNAVAILABLE

    assert "Authentication failed while fetching uptimerobot data" in caplog.text

    assert len(flows) == 1
    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN
    assert flow["context"]["source"] == config_entries.SOURCE_REAUTH
    assert flow["context"]["entry_id"] == mock_config_entry.entry_id