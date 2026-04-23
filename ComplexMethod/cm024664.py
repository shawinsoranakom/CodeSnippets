async def test_subscribe(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    test_entity: TodoListEntity,
) -> None:
    """Test subscribing to todo updates."""

    await create_mock_platform(hass, [test_entity])

    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {
            "type": "todo/item/subscribe",
            "entity_id": test_entity.entity_id,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None
    subscription_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == subscription_id
    assert msg["type"] == "event"
    event_message = msg["event"]
    assert event_message == {
        "items": [
            {
                "summary": "Item #1",
                "uid": "1",
                "status": "needs_action",
                "due": None,
                "description": None,
                "completed": None,
            },
            {
                "summary": "Item #2",
                "uid": "2",
                "status": "completed",
                "due": None,
                "description": None,
                "completed": None,
            },
        ]
    }
    test_entity._attr_todo_items = [
        *test_entity._attr_todo_items,
        TodoItem(summary="Item #3", uid="3", status=TodoItemStatus.NEEDS_ACTION),
    ]

    test_entity.async_write_ha_state()
    msg = await client.receive_json()
    event_message = msg["event"]
    assert event_message == {
        "items": [
            {
                "summary": "Item #1",
                "uid": "1",
                "status": "needs_action",
                "due": None,
                "description": None,
                "completed": None,
            },
            {
                "summary": "Item #2",
                "uid": "2",
                "status": "completed",
                "due": None,
                "description": None,
                "completed": None,
            },
            {
                "summary": "Item #3",
                "uid": "3",
                "status": "needs_action",
                "due": None,
                "description": None,
                "completed": None,
            },
        ]
    }

    test_entity._attr_todo_items = None
    test_entity.async_write_ha_state()
    msg = await client.receive_json()
    event_message = msg["event"]
    assert event_message == {
        "items": [],
    }