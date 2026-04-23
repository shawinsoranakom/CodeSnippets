async def test_multiple_attrs(hass: HomeAssistant) -> None:
    """Test turn on with multiple attributes."""
    hass.states.async_set(ENTITY_1, STATE_OFF, {})

    turn_on_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_ON)
    turn_off_calls = async_mock_service(hass, DOMAIN, SERVICE_TURN_OFF)
    mode_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_MODE)
    humidity_calls = async_mock_service(hass, DOMAIN, SERVICE_SET_HUMIDITY)

    await async_reproduce_states(
        hass, [State(ENTITY_1, STATE_ON, {ATTR_MODE: MODE_NORMAL, ATTR_HUMIDITY: 45})]
    )

    await hass.async_block_till_done()

    assert len(turn_on_calls) == 1
    assert turn_on_calls[0].data == {"entity_id": ENTITY_1}
    assert len(turn_off_calls) == 0
    assert len(mode_calls) == 1
    assert mode_calls[0].data == {"entity_id": ENTITY_1, "mode": "normal"}
    assert len(humidity_calls) == 1
    assert humidity_calls[0].data == {"entity_id": ENTITY_1, "humidity": 45}