async def test_event(hass: HomeAssistant, client: MagicMock) -> None:
    """Test spa fault event."""
    await init_integration(hass)

    # check the state is unknown
    state = hass.states.get(ENTITY_EVENT)
    assert state.state == STATE_UNKNOWN

    # set a fault
    client.fault = MagicMock(
        fault_datetime=datetime(2025, 2, 15, 13, 0), message_code=16
    )
    client.emit("")
    await hass.async_block_till_done()

    # check new state is what we expect
    state = hass.states.get(ENTITY_EVENT)
    assert state.attributes[ATTR_EVENT_TYPE] == "low_flow"
    assert state.attributes[FAULT_DATE] == "2025-02-15T13:00:00"
    assert state.attributes["code"] == 16

    # set fault to None
    client.fault = None
    client.emit("")
    await hass.async_block_till_done()

    # validate state remains unchanged
    state = hass.states.get(ENTITY_EVENT)
    assert state.attributes[ATTR_EVENT_TYPE] == "low_flow"
    assert state.attributes[FAULT_DATE] == "2025-02-15T13:00:00"
    assert state.attributes["code"] == 16

    # set fault to an unknown one
    client.fault = MagicMock(
        fault_datetime=datetime(2025, 2, 15, 14, 0), message_code=-1
    )
    # validate a ValueError is raises
    with pytest.raises(ValueError):
        client.emit("")
    await hass.async_block_till_done()

    # validate state remains unchanged
    state = hass.states.get(ENTITY_EVENT)
    assert state.attributes[ATTR_EVENT_TYPE] == "low_flow"
    assert state.attributes[FAULT_DATE] == "2025-02-15T13:00:00"
    assert state.attributes["code"] == 16