async def test_async_subscribe_updates(
    hass: HomeAssistant, test_entity: TodoListEntity
) -> None:
    """Test async_subscribe_updates delivers list updates to listeners."""
    await create_mock_platform(hass, [test_entity])

    received_updates: list[list[TodoItem] | None] = []

    def listener(items: list[TodoItem] | None) -> None:
        received_updates.append(items)

    unsub = test_entity.async_subscribe_updates(listener)

    # Trigger an update
    test_entity.async_write_ha_state()

    assert len(received_updates) == 1
    items = received_updates[0]
    assert len(items) == 2
    assert isinstance(items[0], TodoItem)
    assert items[0].summary == "Item #1"
    assert items[0].uid == "1"
    assert items[0].status == TodoItemStatus.NEEDS_ACTION
    assert isinstance(items[1], TodoItem)
    assert items[1].summary == "Item #2"
    assert items[1].uid == "2"
    assert items[1].status == TodoItemStatus.COMPLETED

    # Verify items are copies (not the same objects)
    assert items[0] is not test_entity.todo_items[0]
    assert items[1] is not test_entity.todo_items[1]

    # Add a new item and trigger update
    test_entity._attr_todo_items = [
        *test_entity._attr_todo_items,
        TodoItem(summary="Item #3", uid="3", status=TodoItemStatus.NEEDS_ACTION),
    ]
    test_entity.async_write_ha_state()

    assert len(received_updates) == 2
    items = received_updates[1]
    assert len(items) == 3
    assert items[2].summary == "Item #3"

    # Set items to None and trigger update
    test_entity._attr_todo_items = None
    test_entity.async_write_ha_state()
    assert len(received_updates) == 3
    assert received_updates[2] is None

    # Add a new item to make it available again and trigger update
    test_entity._attr_todo_items = [
        TodoItem(summary="New item", uid="4", status=TodoItemStatus.NEEDS_ACTION)
    ]
    test_entity.async_write_ha_state()
    assert len(received_updates) == 4
    items = received_updates[3]
    assert len(items) == 1
    assert items[0].summary == "New item"
    assert items[0].uid == "4"
    assert items[0].status == TodoItemStatus.NEEDS_ACTION

    # Unsubscribe and verify no more updates
    unsub()
    test_entity.async_write_ha_state()
    assert len(received_updates) == 4