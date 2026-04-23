async def test_ws_reorder_items(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sl_setup: None,
    snapshot: SnapshotAssertion,
) -> None:
    """Test reordering shopping_list items websocket command."""
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "beer"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "wine"}}
    )
    await intent.async_handle(
        hass, "test", "HassShoppingListAddItem", {"item": {"value": "apple"}}
    )
    assert_shopping_list_data(hass, snapshot)

    beer_id = hass.data["shopping_list"].items[0]["id"]
    wine_id = hass.data["shopping_list"].items[1]["id"]
    apple_id = hass.data["shopping_list"].items[2]["id"]

    client = await hass_ws_client(hass)
    events = async_capture_events(hass, EVENT_SHOPPING_LIST_UPDATED)
    await client.send_json(
        {
            "id": 6,
            "type": "shopping_list/items/reorder",
            "item_ids": [wine_id, apple_id, beer_id],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    assert len(events) == 1
    assert hass.data["shopping_list"].items[0] == {
        "id": wine_id,
        "name": "wine",
        "complete": False,
    }
    assert hass.data["shopping_list"].items[1] == {
        "id": apple_id,
        "name": "apple",
        "complete": False,
    }
    assert hass.data["shopping_list"].items[2] == {
        "id": beer_id,
        "name": "beer",
        "complete": False,
    }
    assert_shopping_list_data(hass, snapshot)

    # Mark wine as completed.
    await client.send_json(
        {
            "id": 7,
            "type": "shopping_list/items/update",
            "item_id": wine_id,
            "complete": True,
        }
    )
    _ = await client.receive_json()
    assert len(events) == 2
    assert_shopping_list_data(hass, snapshot)

    await client.send_json(
        {
            "id": 8,
            "type": "shopping_list/items/reorder",
            "item_ids": [apple_id, beer_id],
        }
    )
    msg = await client.receive_json()
    assert msg["success"] is True
    assert len(events) == 3
    assert hass.data["shopping_list"].items[0] == {
        "id": apple_id,
        "name": "apple",
        "complete": False,
    }
    assert hass.data["shopping_list"].items[1] == {
        "id": beer_id,
        "name": "beer",
        "complete": False,
    }
    assert hass.data["shopping_list"].items[2] == {
        "id": wine_id,
        "name": "wine",
        "complete": True,
    }
    assert_shopping_list_data(hass, snapshot)