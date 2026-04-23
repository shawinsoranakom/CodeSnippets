async def test_ws_update_item(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test update shopping_list item websocket command."""
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    assert_shopping_list_data(hass, snapshot)

    beer_id = hass.data["shopping_list"].items[0]["id"]
    wine_id = hass.data["shopping_list"].items[1]["id"]
    client = await hass_ws_client(hass)
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    await client.send_json(
        {
            "id": 5,
            "type": "shopping_list/items/update",
            "item_id": beer_id,
            "name": "soda",
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data == {"id": beer_id, "name": "soda", "complete": False}
    assert len(events) == 1
    assert_shopping_list_data(hass, snapshot)

    await client.send_json(
        {
            "id": 6,
            "type": "shopping_list/items/update",
            "item_id": wine_id,
            "complete": True,
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data == {"id": wine_id, "name": "wine", "complete": True}
    assert len(events) == 2
    assert_shopping_list_data(hass, snapshot)

    beer, wine = hass.data["shopping_list"].items
    assert beer == {"id": beer_id, "name": "soda", "complete": False}
    assert wine == {"id": wine_id, "name": "wine", "complete": True}