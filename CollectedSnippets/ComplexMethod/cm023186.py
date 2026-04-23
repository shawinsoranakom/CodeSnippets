async def test_invoke_cc_api(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    climate_danfoss_lc_13,
    climate_radio_thermostat_ct100_plus_different_endpoints,
    integration,
) -> None:
    """Test invoke_cc_api service."""
    device_radio_thermostat = device_registry.async_get_device(
        identifiers={
            get_device_id(
                client.driver, climate_radio_thermostat_ct100_plus_different_endpoints
            )
        }
    )
    assert device_radio_thermostat
    device_danfoss = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, climate_danfoss_lc_13)}
    )
    assert device_danfoss

    # Test successful invoke_cc_api call with a static endpoint
    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.return_value = {"response": True}

    await hass.services.async_call(
        DOMAIN,
        SERVICE_INVOKE_CC_API,
        {
            ATTR_DEVICE_ID: [
                device_radio_thermostat.id,
                device_danfoss.id,
            ],
            ATTR_COMMAND_CLASS: 67,
            ATTR_ENDPOINT: 0,
            ATTR_METHOD_NAME: "someMethod",
            ATTR_PARAMETERS: [1, 2],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()

    # Test successful invoke_cc_api call without an endpoint (include area)
    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(device_danfoss.id, area_id=area.id)

    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.return_value = {"response": True}

    await hass.services.async_call(
        DOMAIN,
        SERVICE_INVOKE_CC_API,
        {
            ATTR_AREA_ID: area.id,
            ATTR_DEVICE_ID: [
                device_radio_thermostat.id,
                "fake_device_id",
            ],
            ATTR_ENTITY_ID: [
                "sensor.not_real",
                "select.living_connect_z_thermostat_local_protection_state",
                "sensor.living_connect_z_thermostat_node_status",
            ],
            ATTR_COMMAND_CLASS: 67,
            ATTR_METHOD_NAME: "someMethod",
            ATTR_PARAMETERS: [1, 2],
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()

    # Test failed invoke_cc_api call on one node. We return the error on
    # the first node in the call to make sure that gather works as expected
    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.side_effect = FailedZWaveCommand(
        "test", 12, "test"
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_INVOKE_CC_API,
            {
                ATTR_DEVICE_ID: [
                    device_danfoss.id,
                    device_radio_thermostat.id,
                ],
                ATTR_COMMAND_CLASS: 67,
                ATTR_ENDPOINT: 0,
                ATTR_METHOD_NAME: "someMethod",
                ATTR_PARAMETERS: [1, 2],
            },
            blocking=True,
        )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert (
        args["nodeId"]
        == climate_radio_thermostat_ct100_plus_different_endpoints.node_id
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 67
    assert args["endpoint"] == 0
    assert args["methodName"] == "someMethod"
    assert args["args"] == [1, 2]
    assert args["nodeId"] == climate_danfoss_lc_13.node_id

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()