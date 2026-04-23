async def test_subscribe(
    hass: HomeAssistant,
    setup_integration: None,
    api: AsyncMock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test for subscribing to state updates."""

    # Subscribe and get the initial list
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "todo/item/subscribe",
            "entity_id": "todo.name",
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
    assert items[0]["summary"] == "Cheese"
    assert items[0]["status"] == "needs_action"
    assert items[0]["uid"]

    # Fake API response when state is refreshed
    api.get_tasks.side_effect = make_api_response(
        [make_api_task(id="test-id-1", content="Wine", completed_at=None)]
    )
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "Cheese", ATTR_RENAME: "Wine"},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
    )

    # Verify update is published
    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    items = msg["event"].get("items")
    assert items
    assert len(items) == 1
    assert items[0]["summary"] == "Wine"
    assert items[0]["status"] == "needs_action"
    assert items[0]["uid"]