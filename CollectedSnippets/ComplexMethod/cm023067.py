async def test_caching_behavior(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_predict_common_control: Mock,
) -> None:
    """Test that results are cached for 24 hours."""
    assert await async_setup_component(hass, "usage_prediction", {})

    client = await hass_ws_client(hass)

    # First call should fetch from database
    with freeze_time(NOW):
        await client.send_json({"id": 1, "type": "usage_prediction/common_control"})
        msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"] == {
        "entities": [
            "light.kitchen",
        ]
    }
    assert mock_predict_common_control.call_count == 1

    new_result = deepcopy(mock_predict_common_control.return_value)
    new_result.morning.append("light.bla")
    mock_predict_common_control.return_value = new_result

    # Second call within 24 hours should use cache
    with freeze_time(NOW + timedelta(hours=23)):
        await client.send_json({"id": 2, "type": "usage_prediction/common_control"})
        msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"] == {
        "entities": [
            "light.kitchen",
        ]
    }
    # Should still be 1 (no new database call)
    assert mock_predict_common_control.call_count == 1

    # Third call after 24 hours should fetch from database again
    with freeze_time(NOW + timedelta(hours=25)):
        await client.send_json({"id": 3, "type": "usage_prediction/common_control"})
        msg = await client.receive_json()

    assert msg["success"] is True
    assert msg["result"] == {"entities": ["light.kitchen", "light.bla"]}
    # Should now be 2 (new database call)
    assert mock_predict_common_control.call_count == 2