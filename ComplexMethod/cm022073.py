async def test_subscribe_item(
    hass: HomeAssistant,
    sl_setup: None,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test updating a todo item."""

    # Create new item
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {
            ATTR_ITEM: "soda",
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Subscribe and get the initial list
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "todo/item/subscribe",
            "entity_id": TEST_ENTITY,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    items = msg["event"].get("items")
    assert items
    assert len(items) == 1
    assert items[0]["summary"] == "soda"
    assert items[0]["status"] == "needs_action"
    uid = items[0]["uid"]
    assert uid

    # Rename item item completed
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {
            ATTR_ITEM: "soda",
            ATTR_RENAME: "milk",
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Verify update is published
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    items = msg["event"].get("items")
    assert items
    assert len(items) == 1
    assert items[0]["summary"] == "milk"
    assert items[0]["status"] == "needs_action"
    assert "uid" in items[0]