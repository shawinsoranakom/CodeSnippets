async def test_valve_set_state(
    hass: HomeAssistant, hk_driver, events: list[Event]
) -> None:
    """Test if Valve accessory and HA are updated accordingly."""
    entity_id = "valve.valve_test"

    hass.states.async_set(entity_id, None)
    await hass.async_block_till_done()

    acc = Valve(hass, hk_driver, "Valve", entity_id, 5, {CONF_TYPE: TYPE_VALVE})
    acc.run()
    await hass.async_block_till_done()

    assert acc.aid == 5
    assert acc.category == 29  # Faucet

    assert acc.char_active.value == 0
    assert acc.char_in_use.value == 0
    assert acc.char_valve_type.value == 0  # Generic Valve

    hass.states.async_set(entity_id, STATE_OPEN)
    await hass.async_block_till_done()
    assert acc.char_active.value == 1
    assert acc.char_in_use.value == 1

    hass.states.async_set(entity_id, STATE_CLOSED)
    await hass.async_block_till_done()
    assert acc.char_active.value == 0
    assert acc.char_in_use.value == 0

    # Set from HomeKit
    call_turn_on = async_mock_service(hass, "valve", SERVICE_OPEN_VALVE)
    call_turn_off = async_mock_service(hass, "valve", SERVICE_CLOSE_VALVE)

    acc.char_active.client_update_value(1)
    await hass.async_block_till_done()
    assert acc.char_in_use.value == 1
    assert call_turn_on
    assert call_turn_on[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 1
    assert events[-1].data[ATTR_VALUE] is None

    acc.char_active.client_update_value(0)
    await hass.async_block_till_done()
    assert acc.char_in_use.value == 0
    assert call_turn_off
    assert call_turn_off[0].data[ATTR_ENTITY_ID] == entity_id
    assert len(events) == 2
    assert events[-1].data[ATTR_VALUE] is None