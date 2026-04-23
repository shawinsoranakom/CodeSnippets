async def test_common_control(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    mock_predict_common_control: Mock,
) -> None:
    """Test usage_prediction common control WebSocket command."""
    assert await async_setup_component(hass, "usage_prediction", {})

    client = await hass_ws_client(hass)

    with freeze_time(NOW):
        await client.send_json({"id": 1, "type": "usage_prediction/common_control"})
        msg = await client.receive_json()

    assert msg["id"] == 1
    assert msg["type"] == "result"
    assert msg["success"] is True
    assert msg["result"] == {
        "entities": [
            "light.kitchen",
        ]
    }
    assert mock_predict_common_control.call_count == 1
    assert mock_predict_common_control.mock_calls[0][1][1] == hass_admin_user.id