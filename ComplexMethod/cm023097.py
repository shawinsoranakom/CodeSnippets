async def test_thermostat_v2(
    hass: HomeAssistant,
    client,
    climate_radio_thermostat_ct100_plus,
    integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test a thermostat v2 command class entity."""
    node = climate_radio_thermostat_ct100_plus
    state = hass.states.get(CLIMATE_RADIO_THERMOSTAT_ENTITY)

    assert state
    assert state.state == HVACMode.HEAT
    assert state.attributes[ATTR_HVAC_MODES] == [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
    ]
    assert state.attributes[ATTR_CURRENT_HUMIDITY] == 30
    assert state.attributes[ATTR_CURRENT_TEMPERATURE] == 22.2
    assert state.attributes[ATTR_TEMPERATURE] == 22.2
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert state.attributes[ATTR_TARGET_TEMP_LOW] is None
    assert state.attributes[ATTR_HVAC_ACTION] == HVACAction.IDLE
    assert state.attributes[ATTR_FAN_MODE] == "Auto low"
    assert state.attributes[ATTR_FAN_STATE] == "Idle / off"
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    client.async_send_command.reset_mock()

    # Check that turning the device on is a no-op because it is already on
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 0

    client.async_send_command.reset_mock()

    # Test setting hvac mode
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_HVAC_MODE: HVACMode.COOL,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 1,
        "property": "mode",
    }
    assert args["value"] == 2

    client.async_send_command.reset_mock()

    # Test setting temperature
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_HVAC_MODE: HVACMode.COOL,
            ATTR_TEMPERATURE: 25,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "commandClass": 64,
        "endpoint": 1,
        "property": "mode",
    }
    assert args["value"] == 2
    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "commandClass": 67,
        "endpoint": 1,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 77

    client.async_send_command.reset_mock()

    # Test cool mode update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 13,
            "args": {
                "commandClassName": "Thermostat Mode",
                "commandClass": 64,
                "endpoint": 1,
                "property": "mode",
                "propertyName": "mode",
                "newValue": 2,
                "prevValue": 1,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(CLIMATE_RADIO_THERMOSTAT_ENTITY)
    assert state.state == HVACMode.COOL
    assert state.attributes[ATTR_TEMPERATURE] == 22.8
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] is None
    assert state.attributes[ATTR_TARGET_TEMP_LOW] is None

    # Test heat_cool mode update from value updated event
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 13,
            "args": {
                "commandClassName": "Thermostat Mode",
                "commandClass": 64,
                "endpoint": 1,
                "property": "mode",
                "propertyName": "mode",
                "newValue": 3,
                "prevValue": 1,
            },
        },
    )
    node.receive_event(event)

    state = hass.states.get(CLIMATE_RADIO_THERMOSTAT_ENTITY)
    assert state.state == HVACMode.HEAT_COOL
    assert state.attributes[ATTR_TEMPERATURE] is None
    assert state.attributes[ATTR_TARGET_TEMP_HIGH] == 22.8
    assert state.attributes[ATTR_TARGET_TEMP_LOW] == 22.2

    client.async_send_command.reset_mock()

    # Test setting temperature with heat_cool
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_TARGET_TEMP_HIGH: 30,
            ATTR_TARGET_TEMP_LOW: 25,
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 2
    args = client.async_send_command.call_args_list[0][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "commandClass": 67,
        "endpoint": 1,
        "property": "setpoint",
        "propertyKey": 1,
    }
    assert args["value"] == 77

    args = client.async_send_command.call_args_list[1][0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "commandClass": 67,
        "endpoint": 1,
        "property": "setpoint",
        "propertyKey": 2,
    }
    assert args["value"] == 86

    client.async_send_command.reset_mock()

    # Test setting invalid hvac mode
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {
                ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
                ATTR_HVAC_MODE: HVACMode.DRY,
            },
            blocking=True,
        )

    client.async_send_command.reset_mock()

    # Test setting fan mode
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
            ATTR_FAN_MODE: "Low",
        },
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "endpoint": 1,
        "commandClass": 68,
        "property": "mode",
    }
    assert args["value"] == 1

    client.async_send_command.reset_mock()

    # Test turning device off then on to see if the previous state is retained
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "endpoint": 1,
        "commandClass": 64,
        "property": "mode",
    }
    assert args["value"] == 0

    # Update state to off
    event = Event(
        type="value updated",
        data={
            "source": "node",
            "event": "value updated",
            "nodeId": 13,
            "args": {
                "commandClassName": "Thermostat Mode",
                "commandClass": 64,
                "endpoint": 1,
                "property": "mode",
                "propertyName": "mode",
                "newValue": 0,
                "prevValue": 3,
            },
        },
    )
    node.receive_event(event)

    client.async_send_command.reset_mock()

    # Test turning device on
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY},
        blocking=True,
    )

    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "node.set_value"
    assert args["nodeId"] == 13
    assert args["valueId"] == {
        "endpoint": 1,
        "commandClass": 64,
        "property": "mode",
    }
    assert args["value"] == 3

    client.async_send_command.reset_mock()

    # Test setting invalid fan mode
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {
                ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
                ATTR_FAN_MODE: "fake value",
            },
            blocking=True,
        )

    # Refresh value should log an error when there is an issue
    client.async_send_command.reset_mock()
    client.async_send_command.side_effect = FailedZWaveCommand("test", 1, "test")
    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_VALUE,
        {
            ATTR_ENTITY_ID: CLIMATE_RADIO_THERMOSTAT_ENTITY,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert "Error while refreshing value" in caplog.text