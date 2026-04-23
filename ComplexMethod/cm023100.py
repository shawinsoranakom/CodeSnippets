async def test_setpoint_thermostat(
    hass: HomeAssistant, client, climate_danfoss_lc_13, integration
) -> None:
    """Test a setpoint thermostat command class entity."""
    node = climate_danfoss_lc_13
    state = hass.states.get(CLIMATE_DANFOSS_LC13_ENTITY)

    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 14
    assert state.attributes[ATTR_HVAC_MODES] == [HVACMode.HEAT]
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == ClimateEntityFeature.TARGET_TEMPERATURE
    )

    client.async_send_command_no_wait.reset_mock()

    # Test setting temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
            ATTR_TEMPERATURE: 21.5,
        },
        blocking=True,
    )

    # Test setting illegal mode raises an error
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
                ATTR_HVAC_MODE: HVACMode.COOL,
            },
            blocking=True,
        )

    # Test that setting HVACMode.HEAT works. If the no-op logic didn't work, this would
    # raise an error
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: CLIMATE_DANFOSS_LC13_ENTITY,
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 5
    assert args["valueId"] == {
        "endpoint": 0,
        "commandClass": 67,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 21.5

    client.async_send_command_no_wait.reset_mock()

    # Test setpoint mode update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 5,
            "args": {
                "commandClassName": "Thermostat Setpoint",
                "commandClass": 67,
                "endpoint": 0,
                "property": "setpoint",
                "propertyKey": 1,
                "propertyKeyName": "Heating",
                "propertyName": "setpoint",
                "newValue": 23,
                "prevValue": 21.5,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(CLIMATE_DANFOSS_LC13_ENTITY)
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_TEMPERATURE] == 23

    client.async_send_command_no_wait.reset_mock()