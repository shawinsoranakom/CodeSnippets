async def test_call_service_blocking(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket, command
) -> None:
    """Test call service commands block, except for homeassistant restart / stop."""
    async_mock_service(
        hass,
        "domain_test",
        "test_service",
        response={"hello": "world"},
        supports_response=SupportsResponse.OPTIONAL,
    )
    with patch(
        "homeassistant.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        mock_call.return_value = {"foo": "bar"}
        await websocket_client.send_json_auto_id(
            {
                "type": "call_service",
                "domain": "domain_test",
                "service": "test_service",
                "service_data": {"hello": "world"},
                "return_response": True,
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    assert msg["result"]["response"] == {"foo": "bar"}
    mock_call.assert_called_once_with(
        ANY,
        "domain_test",
        "test_service",
        {"hello": "world"},
        blocking=True,
        context=ANY,
        target=ANY,
        return_response=True,
    )

    with patch(
        "homeassistant.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        mock_call.return_value = None
        await websocket_client.send_json_auto_id(
            {
                "type": "call_service",
                "domain": "domain_test",
                "service": "test_service",
                "service_data": {"hello": "world"},
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY,
        "domain_test",
        "test_service",
        {"hello": "world"},
        blocking=True,
        context=ANY,
        target=ANY,
        return_response=False,
    )

    async_mock_service(hass, "homeassistant", "test_service")
    with patch(
        "homeassistant.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        mock_call.return_value = None
        await websocket_client.send_json_auto_id(
            {
                "type": "call_service",
                "domain": "homeassistant",
                "service": "test_service",
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY,
        "homeassistant",
        "test_service",
        ANY,
        blocking=True,
        context=ANY,
        target=ANY,
        return_response=False,
    )

    async_mock_service(hass, "homeassistant", "restart")
    with patch(
        "homeassistant.core.ServiceRegistry.async_call", autospec=True
    ) as mock_call:
        mock_call.return_value = None
        await websocket_client.send_json_auto_id(
            {
                "type": "call_service",
                "domain": "homeassistant",
                "service": "restart",
            },
        )
        msg = await websocket_client.receive_json()

    assert msg["type"] == const.TYPE_RESULT
    assert msg["success"]
    mock_call.assert_called_once_with(
        ANY,
        "homeassistant",
        "restart",
        ANY,
        blocking=True,
        context=ANY,
        target=ANY,
        return_response=False,
    )