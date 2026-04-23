async def test_rain_sensor_unavailability(
    hass: HomeAssistant,
    mock_window: MagicMock,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test rain sensor becomes unavailable on errors and logs appropriately."""

    test_entity_id = "binary_sensor.test_window_rain_sensor"

    # Entity should be available initially
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE

    # Simulate communication error
    mock_window.get_limitation_min.side_effect = PyVLXException("Connection failed")
    await update_polled_entities(hass, freezer)

    # Entity should now be unavailable
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    # Verify unavailability was logged once
    assert (
        "Rain sensor binary_sensor.test_window_rain_sensor is unavailable"
        in caplog.text
    )
    assert "Connection failed" in caplog.text
    caplog.clear()

    # Another update attempt should not log again (already logged)
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state.state == STATE_UNAVAILABLE
    assert "is unavailable" not in caplog.text
    caplog.clear()

    # Simulate recovery
    mock_window.get_limitation_min.side_effect = None
    mock_window.get_limitation_min.return_value.position_percent = 0
    await update_polled_entities(hass, freezer)

    # Entity should be available again
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_OFF

    # Verify recovery was logged
    assert (
        "Rain sensor binary_sensor.test_window_rain_sensor is back online"
        in caplog.text
    )
    caplog.clear()

    # Another successful update should not log recovery again
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state.state == STATE_OFF
    assert "back online" not in caplog.text