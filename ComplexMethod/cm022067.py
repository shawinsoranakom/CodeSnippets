async def test_get_items(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sl_setup: None,
    ws_get_items: WsGetItemsType,
) -> None:
    """Test creating a shopping list item with the WS API and verifying with To-do API."""
    client = await hass_ws_client(hass)

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"

    # Native shopping list websocket
    await client.send_json_auto_id({"type": "shopping_list/items/add", "name": "soda"})
    msg = await client.receive_json()
    assert msg["success"] is True
    data = msg["result"]
    assert data["name"] == "soda"
    assert data["complete"] is False

    # Fetch items using To-do platform
    items = await ws_get_items()
    assert len(items) == 1
    assert items[0]["summary"] == "soda"
    assert items[0]["status"] == "needs_action"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"