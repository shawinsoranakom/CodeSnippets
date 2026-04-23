async def test_rain_sensor_state(
    hass: HomeAssistant,
    mock_window: MagicMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the rain sensor."""

    test_entity_id = "binary_sensor.test_window_rain_sensor"

    # simulate no rain detected
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_OFF

    # simulate rain detected (Velux GPU reports 100)
    mock_window.get_limitation_min.return_value.position_percent = 100
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # simulate rain detected (most Velux models report 93)
    mock_window.get_limitation_min.return_value.position_percent = 93
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # simulate rain detected (other Velux models report 89)
    mock_window.get_limitation_min.return_value.position_percent = 89
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_ON

    # simulate other limits which do not indicate rain detected
    mock_window.get_limitation_min.return_value.position_percent = 88
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_OFF

    # simulate no rain detected again
    mock_window.get_limitation_min.return_value.position_percent = 0
    await update_polled_entities(hass, freezer)
    state = hass.states.get(test_entity_id)
    assert state is not None
    assert state.state == STATE_OFF