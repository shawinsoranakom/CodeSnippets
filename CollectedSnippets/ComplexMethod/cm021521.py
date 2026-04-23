async def test_trigger_attributes_with_optimistic_state(
    hass: HomeAssistant,
    attr: str,
    expected: str,
    calls: list[ServiceCall],
) -> None:
    """Test attributes when trigger entity is optimistic."""
    hass.states.async_set(TEST_SWITCH.entity_id, STATE_OFF)
    await hass.async_block_till_done()

    state = hass.states.get(TEST_SWITCH.entity_id)
    assert state.state == STATE_OFF
    assert state.attributes.get(attr) is None

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )

    state = hass.states.get(TEST_SWITCH.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get(attr) is None

    assert_action(TEST_SWITCH, calls, 1, "turn_on")

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )

    state = hass.states.get(TEST_SWITCH.entity_id)
    assert state.state == STATE_OFF
    assert state.attributes.get(attr) is None

    assert_action(TEST_SWITCH, calls, 2, "turn_off")

    await async_trigger(hass, TEST_SENSOR, expected)

    state = hass.states.get(TEST_SWITCH.entity_id)
    assert state.state == STATE_OFF
    assert state.attributes.get(attr) == expected

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: TEST_SWITCH.entity_id},
        blocking=True,
    )

    state = hass.states.get(TEST_SWITCH.entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get(attr) == expected

    assert_action(TEST_SWITCH, calls, 3, "turn_on")