async def test_susbcribe(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test subscribing to item updates."""

    assert await integration_setup()

    # Subscribe and get the initial list
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "todo/item/subscribe",
            "entity_id": "todo.my_tasks",
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
    assert items[0]["summary"] == "Water"
    assert items[0]["status"] == "needs_action"
    uid = items[0]["uid"]
    assert uid

    # Rename item
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: uid, ATTR_RENAME: "Milk"},
        target={ATTR_ENTITY_ID: "todo.my_tasks"},
        blocking=True,
    )

    # Verify update is published
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    items = msg["event"].get("items")
    assert items
    assert len(items) == 1
    assert items[0]["summary"] == "Milk"
    assert items[0]["status"] == "needs_action"
    assert "uid" in items[0]