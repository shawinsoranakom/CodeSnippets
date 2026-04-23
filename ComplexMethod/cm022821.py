async def test_subscribe(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    dav_client: Mock,
    calendar: Mock,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test subscription to item updates."""

    item = Todo(dav_client, None, TODO_NEEDS_ACTION, calendar, "2")
    calendar.search = MagicMock(return_value=[item])

    await hass.config_entries.async_setup(config_entry.entry_id)

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
    assert items[0]["summary"] == "Cheese"
    assert items[0]["status"] == "needs_action"
    assert items[0]["uid"]

    calendar.todo_by_uid = MagicMock(return_value=item)
    dav_client.put.return_value.status = 204
    # Reflect update for state refresh after update
    calendar.search.return_value = [
        Todo(
            dav_client, None, TODO_NEEDS_ACTION.replace("Cheese", "Milk"), calendar, "2"
        )
    ]
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {
            ATTR_ITEM: "Cheese",
            ATTR_RENAME: "Milk",
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
    assert items[0]["summary"] == "Milk"
    assert items[0]["status"] == "needs_action"
    assert items[0]["uid"]