async def test_set_system_data(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_storage: dict[str, Any],
    subscriptions: list[tuple[int, dict[str, str], Any]],
    events: list[list[tuple[int, Any]]],
) -> None:
    """Test set_system_data command with initial data."""
    storage_key = f"{DOMAIN}.system_data"
    hass_storage[storage_key] = {
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": "string"},
    }

    client = await hass_ws_client(hass)

    for msg_id, key, event_data in subscriptions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "frontend/subscribe_system_data",
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
        {
            "id": 5,
            "type": "frontend/set_system_data",
            "key": "test-non-existent-key",
            "value": "test-value-new",
        }
    )

    for msg_id, event_data in events[0]:
        event = await client.receive_json()
        assert event == {"id": msg_id, "type": "event", "event": {"value": event_data}}

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 6, "type": "frontend/get_system_data", "key": "test-non-existent-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value-new"

    # test updating with complex data

    await client.send_json(
        {
            "id": 7,
            "type": "frontend/set_system_data",
            "key": "test-complex",
            "value": [{"foo": "bar"}],
        }
    )

    for msg_id, event_data in events[1]:
        event = await client.receive_json()
        assert event == {"id": msg_id, "type": "event", "event": {"value": event_data}}

    res = await client.receive_json()
    assert res["success"], res

    await client.send_json(
        {"id": 8, "type": "frontend/get_system_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"][0]["foo"] == "bar"

    # ensure other existing key was not modified

    await client.send_json(
        {"id": 9, "type": "frontend/get_system_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"