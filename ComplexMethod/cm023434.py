async def test_reproducing_on_off_states(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test reproducing humidifier states."""
    hass.states.async_set(ENTITY_1, "off", {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 45})
    hass.states.async_set(ENTITY_2, "on", {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 45})

    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    turn_off_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)
    mode_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    humidity_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [
            State(ENTITY_1, "off", {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 45}),
            State(ENTITY_2, "on", {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 45}),
        ],
    )

    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(mode_calls) == 0
    assert len(humidity_calls) == 0

    # Test invalid state is handled
    await async_reproduce_state(hass, [State(ENTITY_1, "not_supported")])

    assert "not_supported" in caplog.text
    assert len(turn_on_calls) == 0
    assert len(turn_off_calls) == 0
    assert len(mode_calls) == 0
    assert len(humidity_calls) == 0

    # Make sure correct services are called
    await async_reproduce_state(
        hass,
        [
            State(ENTITY_2, "off"),
            State(ENTITY_1, "on", {}),
            # Should not raise
            State("humidifier.non_existing", "on"),
        ],
    )

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].domain == "humidifier"
    assert turn_on_calls[0].data == {"entity_id": ENTITY_1}

    assert len(turn_off_calls) == 1
    assert turn_off_calls[0].domain == "humidifier"
    assert turn_off_calls[0].data == {"entity_id": ENTITY_2}

    # Make sure we didn't call services for missing attributes
    assert len(mode_calls) == 0
    assert len(humidity_calls) == 0