async def test_websocket_bind_unbind_group(
    command_type: str,
    hass: HomeAssistant,
    app_controller: ControllerApplication,
    zha_client,
) -> None:
    """Test websocket API for binding and unbinding devices to groups."""

    test_group_id = 0x0001
    gateway_mock = MagicMock()

    with patch(
        "homeassistant.components.zha.websocket_api.get_zha_gateway",
        return_value=gateway_mock,
    ):
        device_mock = MagicMock()
        bind_mock = AsyncMock()
        unbind_mock = AsyncMock()
        device_mock.async_bind_to_group = bind_mock
        device_mock.async_unbind_from_group = unbind_mock
        gateway_mock.get_device = MagicMock()
        gateway_mock.get_device.return_value = device_mock
        await zha_client.send_json(
            {
                ID: 27,
                TYPE: f"zha/groups/{command_type}",
                ATTR_SOURCE_IEEE: IEEE_SWITCH_DEVICE,
                GROUP_ID: test_group_id,
                BINDINGS: [
                    {
                        ATTR_ENDPOINT_ID: 1,
                        ID: 6,
                        ATTR_NAME: "OnOff",
                        ATTR_TYPE: "out",
                    },
                ],
            }
        )
        msg = await zha_client.receive_json()

    assert msg["id"] == 27
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    if command_type == "bind":
        assert bind_mock.mock_calls == [call(test_group_id, ANY)]
    elif command_type == "unbind":
        assert unbind_mock.mock_calls == [call(test_group_id, ANY)]