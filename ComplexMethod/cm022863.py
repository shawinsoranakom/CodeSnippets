async def test_rate_limit(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    tankerkoenig: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test detection of API rate limit."""
    assert config_entry.state is ConfigEntryState.LOADED
    state = hass.states.get("binary_sensor.station_somewhere_street_1_status")
    assert state
    assert state.state == "on"

    tankerkoenig.prices.side_effect = TankerkoenigRateLimitError
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(minutes=DEFAULT_SCAN_INTERVAL)
    )
    await hass.async_block_till_done()
    assert (
        "API rate limit reached, consider to increase polling interval" in caplog.text
    )
    state = hass.states.get("binary_sensor.station_somewhere_street_1_status")
    assert state
    assert state.state == STATE_UNAVAILABLE

    tankerkoenig.prices.side_effect = None
    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(minutes=DEFAULT_SCAN_INTERVAL * 2)
    )
    await hass.async_block_till_done()
    state = hass.states.get("binary_sensor.station_somewhere_street_1_status")
    assert state
    assert state.state == "on"