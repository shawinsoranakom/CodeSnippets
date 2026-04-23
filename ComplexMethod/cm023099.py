async def test_thermostat_turn_on_after_off_with_resume(
    hass: HomeAssistant, client, aeotec_radiator_thermostat_state, integration
) -> None:
    """Test thermostat that is turned on after starting off with resume support."""
    node_state = copy.deepcopy(aeotec_radiator_thermostat_state)
    # Add resume thermostat mode so we can test that it prefers the resume mode
    value = next(
        value
        for value in node_state["values"]
        if value["commandClass"] == 64 and value["property"] == "mode"
    )
    value["metadata"]["states"] = {
        "0": "Off",
        "5": "Resume (on)",
        "6": "Fan",
        "8": "Dry",
    }
    value["value"] = 0
    node = Node(client, node_state)
    client.driver.controller.emit("node added", {"node": node})
    await hass.async_block_till_done()
    entity_id = "climate.thermostat_hvac"
    assert hass.states.get(entity_id).state == HVACMode.OFF

    client.async_send_command.reset_mock()

    # Test turning device on sends resume command
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 4
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 64,
        "property": "mode",
    }
    assert args["value"] == 5