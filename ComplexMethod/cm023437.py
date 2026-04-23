async def test_state_with_context(hass: HomeAssistant) -> None:
    """Test that context is forwarded."""
    hass.states.async_set(ENTITY_1, STATE_OFF, {})

    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    turn_off_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)
    mode_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    humidity_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)

    context = Context()

    await async_reproduce_states(
        hass,
        [State(ENTITY_1, STATE_ON, {ATTR_MODE: MODE_AWAY, ATTR_HUMIDITY: 45})],
        context=context,
    )

    await hass.async_block_till_done()

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].data == {"entity_id": ENTITY_1}
    assert turn_on_calls[0].context == context
    assert len(turn_off_calls) == 0
    assert len(mode_calls) == 1
    assert mode_calls[0].data == {"entity_id": ENTITY_1, "mode": "away"}
    assert mode_calls[0].context == context
    assert len(humidity_calls) == 1
    assert humidity_calls[0].data == {"entity_id": ENTITY_1, "humidity": 45}
    assert humidity_calls[0].context == context