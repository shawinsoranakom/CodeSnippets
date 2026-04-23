async def test_ws_add_item(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test adding shopping_list item websocket command."""
    client = await hass_ws_client(hass)
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    await client.send_json({"id": 5, "type": "shopping_list/items/add", "name": "soda"})
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data["name"] == "soda"
    assert data["complete"] is False
    assert len(events) == 1
    assert_shopping_list_data(hass, snapshot)

    items = hass.data["shopping_list"].items
    assert len(items) == 1
    assert items[0]["name"] == "soda"
    assert items[0]["complete"] is False