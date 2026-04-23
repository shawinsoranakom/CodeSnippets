async def test_multiple_modes(hass: HomeAssistant) -> None:
    """Test that multiple states gets calls."""
    hass.states.async_set(ENTITY_1, STATE_OFF, {})
    hass.states.async_set(ENTITY_2, STATE_OFF, {})

    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    turn_off_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)
    mode_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    humidity_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)

    await async_reproduce_states(
        hass,
        [
            State(ENTITY_1, STATE_ON, {ATTR_MODE: MODE_ECO, ATTR_HUMIDITY: 40}),
            State(ENTITY_2, STATE_ON, {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 50}),
        ],
    )

    await hass.async_block_till_done()

    assert len(turn_on_calls) == 2
    assert len(turn_off_calls) == 0
    assert len(mode_calls) == 2
    # order is not guaranteed
    assert any(
        call.data == {"entity_id": ENTITY_1, "mode": MODE_ECO} for call in mode_calls
    )
    assert any(
        call.data == {"entity_id": ENTITY_2, "mode": MODE_NORMAL} for call in mode_calls
    )
    assert len(humidity_calls) == 2
    # order is not guaranteed
    assert any(
        call.data == {"entity_id": ENTITY_1, "humidity": 40} for call in humidity_calls
    )
    assert any(
        call.data == {"entity_id": ENTITY_2, "humidity": 50} for call in humidity_calls
    )