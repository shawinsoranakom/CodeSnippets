async def test_execute_script(
    hass: HomeAssistant, websocket_client: MockHAClientWebSocket
) -> None:
    """Test testing a condition."""
    calls = async_mock_service(
        hass, "domain_test", "test_service", response={"hello": "world"}
    )

    await websocket_client.send_json_auto_id(
        {
            "type": "execute_script",
            "sequence": [
                {
                    "service": "domain_test.test_service",
                    "data": {"hello": "world"},
                    "response_variable": "service_result",
                },
                {"stop": "done", "response_variable": "service_result"},
            ],
        }
    )

    msg_no_var = await websocket_client.receive_json()
    assert msg_no_var["type"] == const.TYPE_RESULT
    assert msg_no_var["success"]
    assert msg_no_var["result"]["response"] == {"hello": "world"}

    await websocket_client.send_json_auto_id(
        {
            "type": "execute_script",
            "sequence": {
                "service": "domain_test.test_service",
                "data": {"hello": "{{ name }}"},
            },
            "variables": {"name": "From variable"},
        }
    )

    msg_var = await websocket_client.receive_json()
    assert msg_var["type"] == const.TYPE_RESULT
    assert msg_var["success"]

    await hass.async_block_till_done()
    await hass.async_block_till_done()

    assert len(calls) == 2

    call = calls[0]
    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "world"}
    assert call.context.as_dict() == msg_no_var["result"]["context"]

    call = calls[1]
    assert call.domain == "domain_test"
    assert call.service == "test_service"
    assert call.data == {"hello": "From variable"}
    assert call.context.as_dict() == msg_var["result"]["context"]