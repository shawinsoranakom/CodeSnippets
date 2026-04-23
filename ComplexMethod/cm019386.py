async def test_update_item(
    hass: HomeAssistant,
    setup_integration: None,
    ws_get_items: Callable[[], Awaitable[dict[str, str]]],
    item_data: dict[str, Any],
    expected_item_data: dict[str, Any],
    expected_state: str,
) -> None:
    """Test updating a todo item."""

    # Create new item
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Fetch item
    items = await ws_get_items()
    assert len(items) == 1

    item = items[0]
    assert item["summary"] == "soda"
    assert item["status"] == "needs_action"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"

    # Update item
    update_time = datetime(2023, 11, 18, 8, 0, 0, tzinfo=dt_util.UTC)
    with freeze_time(update_time):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.UPDATE_ITEM,
            {ATTR_ITEM: item["uid"], **item_data},
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    # Verify item is updated
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "soda"
    assert "uid" in item
    del item["uid"]
    assert item == expected_item_data

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == expected_state