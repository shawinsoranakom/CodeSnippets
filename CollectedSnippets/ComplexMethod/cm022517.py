async def test_coordinator_error_handler(
    hass: HomeAssistant,
    mock_peblar: MagicMock,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
    error: Exception,
    log_message: str,
) -> None:
    """Test the coordinators."""
    entity_id = "sensor.peblar_ev_charger_power"

    # Ensure we are set up and the coordinator is working.
    # Confirming this through a sensor entity, that is available.
    assert (state := hass.states.get(entity_id))
    assert state.state != STATE_UNAVAILABLE

    # Mock an error in the coordinator.
    mock_peblar.rest_api.return_value.meter.side_effect = error
    freezer.tick(timedelta(seconds=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Ensure the sensor entity is now unavailable.
    assert (state := hass.states.get(entity_id))
    assert state.state == STATE_UNAVAILABLE

    # Ensure the error is logged
    assert log_message in caplog.text

    # Recover
    mock_peblar.rest_api.return_value.meter.side_effect = None
    freezer.tick(timedelta(seconds=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    # Ensure the sensor entity is now available.
    assert (state := hass.states.get("sensor.peblar_ev_charger_power"))
    assert state.state != STATE_UNAVAILABLE