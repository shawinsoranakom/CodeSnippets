async def test_refresh_notifications(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    client,
    zen_31,
    multisensor_6,
    integration,
) -> None:
    """Test refresh_notifications service."""
    zen_31_device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, zen_31)}
    )
    assert zen_31_device
    multisensor_6_device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, multisensor_6)}
    )
    assert multisensor_6_device

    area = area_registry.async_get_or_create("test")
    device_registry.async_update_device(zen_31_device.id, area_id=area.id)

    # Test successful refresh_notifications call
    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.return_value = {"response": True}

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REFRESH_NOTIFICATIONS,
        {
            ATTR_AREA_ID: area.id,
            ATTR_DEVICE_ID: [zen_31_device.id, multisensor_6_device.id],
            ATTR_NOTIFICATION_TYPE: 1,
            ATTR_NOTIFICATION_EVENT: 2,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 113
    assert args["endpoint"] == 0
    assert args["methodName"] == "get"
    assert args["args"] == [{"notificationType": 1, "notificationEvent": 2}]
    assert args["nodeId"] == zen_31.node_id

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 113
    assert args["endpoint"] == 0
    assert args["methodName"] == "get"
    assert args["args"] == [{"notificationType": 1, "notificationEvent": 2}]
    assert args["nodeId"] == multisensor_6.node_id

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()

    # Test failed refresh_notifications call on one node. We return the error on
    # the first node in the call to make sure that gather works as expected
    client.async_send_command.return_value = {"response": True}
    client.async_send_command_no_wait.side_effect = FailedZWaveCommand(
        "test", 12, "test"
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_REFRESH_NOTIFICATIONS,
            {
                ATTR_DEVICE_ID: [multisensor_6_device.id, zen_31_device.id],
                ATTR_NOTIFICATION_TYPE: 1,
            },
            blocking=True,
        )
    assert len(client.async_send_command.call_args_list) == 1
    args = client.async_send_command.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 113
    assert args["endpoint"] == 0
    assert args["methodName"] == "get"
    assert args["args"] == [{"notificationType": 1}]
    assert args["nodeId"] == zen_31.node_id

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["commandClass"] == 113
    assert args["endpoint"] == 0
    assert args["methodName"] == "get"
    assert args["args"] == [{"notificationType": 1}]
    assert args["nodeId"] == multisensor_6.node_id

    client.async_send_command.reset_mock()
    client.async_send_command_no_wait.reset_mock()