async def test_set_user_data_empty(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[tuple[int, Any]],
) -> None:
    """Test set_user_data command.

    Also test subscribing.
    """
    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_user_data",
            }
            | key
        )

        event = await client.receive_json()
        assert event == {
            "id": msg_id,
            "type": "event",
            "event": {"value": event_data},
        }

        res = await client.receive_json()
        assert res["success"], res

    # test creating

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] is None

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_user_data",
            "key": "test-key",
            "value": "test-value",
        }
    )

    for msg_id, event_data in events:
        event = await client.receive_json()
        assert event == {"id": msg_id, "type": "event", "event": {"value": event_data}}

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 8, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"