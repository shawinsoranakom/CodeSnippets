async def test_invalid_meter_scale(
    hass: HomeAssistant,
    client,
    aeon_smart_switch_6_state,
    integration,
    entity_id: str,
    property_key_name: str,
) -> None:
    """Test a meter sensor with an invalid scale."""
    node_state = copy.deepcopy(aeon_smart_switch_6_state)
    value = next(
        value
        for value in node_state["values"]
        if value["commandClass"] == 50
        and value["property"] == "value"
        and value["propertyKeyName"] == property_key_name
    )
    value["metadata"]["ccSpecific"]["scale"] = -1
    value["metadata"]["unit"] = None

    event = Event(
        "node added",
        {
            "source": "controller",
            "event": "node added",
            "node": node_state,
            "result": {},
        },
    )
    client.driver.controller.receive_event(event)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.attributes[ATTR_METER_TYPE] == MeterType.ELECTRIC.value
    assert state.attributes[ATTR_METER_TYPE_NAME] == MeterType.ELECTRIC.name
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_STATE_CLASS not in state.attributes
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes