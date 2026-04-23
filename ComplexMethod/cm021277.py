async def test_get_user_data(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    hass_storage: dict[str, Any],
) -> None:
    """Test get_user_data command."""
    storage_key = f"{DOMAIN}.user_data_{hass_admin_user.id}"
    hass_storage[storage_key] = {
        "key": storage_key,
        "version": 1,
        "data": {"test-key": "test-value", "test-complex": [{"foo": "bar"}]},
    }

    client = await hass_ws_client(hass)

    # Get a simple string key

    await client.send_json(
        {"id": 6, "type": "frontend/get_user_data", "key": "test-key"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"] == "test-value"

    # Get a more complex key

    await client.send_json(
        {"id": 7, "type": "frontend/get_user_data", "key": "test-complex"}
    )

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"][0]["foo"] == "bar"

    # Get all data (no key)

    await client.send_json({"id": 8, "type": "frontend/get_user_data"})

    res = await client.receive_json()
    assert res["success"], res
    assert res["result"]["value"]["test-key"] == "test-value"
    assert res["result"]["value"]["test-complex"][0]["foo"] == "bar"