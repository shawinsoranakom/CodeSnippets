async def test_ws_get_items(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test get shopping_list items websocket command."""

    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    assert_shopping_list_data(hass, snapshot)

    client = await hass_ws_client(hass)
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)

    await client.send_json({"id": 5, "type": "shopping_list/items"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert len(events) == 0
    assert_shopping_list_data(hass, snapshot)

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    data = msg["result"]
    assert len(data) == 2
    assert data[0]["name"] == "beer"
    assert not data[0]["complete"]
    assert data[1]["name"] == "wine"
    assert not data[1]["complete"]