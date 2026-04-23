async def test_invalid_multilevel_sensor_scale(
    hass: HomeAssistant, client, multisensor_6_state, integration
) -> None:
    """Test a multilevel sensor with an invalid scale."""
    node_state = copy.deepcopy(multisensor_6_state)
    value = next(
        value
        for value in node_state["values"]
        if value["commandClass"] == 49 and value["property"] == "Air temperature"
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

    state = hass.states.get(AIR_TEMPERATURE_SENSOR)

    assert state
    assert state.state == "9.0"
    assert ATTR_UNIT_OF_MEASUREMENT not in state.attributes
    assert ATTR_DEVICE_CLASS not in state.attributes
    assert ATTR_STATE_CLASS not in state.attributes