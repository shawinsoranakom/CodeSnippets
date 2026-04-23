async def test_reset_meter(
    hass: HomeAssistant,
    client,
    aeon_smart_switch_6,
    integration,
    entity_id: str,
) -> None:
    """Test reset_meter service."""
    client.async_send_command.return_value = {}
    client.async_send_command_no_wait.return_value = {}

    # Test successful meter reset call
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_METER,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["nodeId"] == aeon_smart_switch_6.node_id
    assert args["endpoint"] == 0
    assert args["args"] == []

    client.async_send_command_no_wait.reset_mock()

    # Test successful meter reset call with options
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_METER,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_METER_TYPE: 1,
            ATTR_VALUE: 2,
        },
        blocking=True,
    )

    assert len(client.async_send_command_no_wait.call_args_list) == 1
    args = client.async_send_command_no_wait.call_args[0][0]
    assert args["command"] == "endpoint.invoke_cc_api"
    assert args["nodeId"] == aeon_smart_switch_6.node_id
    assert args["endpoint"] == 0
    assert args["args"] == [{"type": 1, "targetValue": 2}]

    client.async_send_command_no_wait.reset_mock()

    client.async_send_command_no_wait.side_effect = FailedZWaveCommand(
        "test", 1, "test"
    )

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_RESET_METER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert str(err.value) == (
        "Failed to reset meters on node Node(node_id=102) endpoint 0: "
        "zwave_error: Z-Wave error 1 - test"
    )