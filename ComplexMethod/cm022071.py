async def test_partial_update_item(
    hass: HomeAssistant,
    sl_setup: None,
    ws_get_items: WsGetItemsType,
) -> None:
    """Test updating a todo item with partial information."""

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

    # Fetch item
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "soda"
    assert item["status"] == "needs_action"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"

    # Mark item completed without changing the summary
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {
            ATTR_ITEM: item["uid"],
            ATTR_STATUS: "completed",
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Verify item is marked as completed
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "soda"
    assert item["status"] == "completed"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"

    # Change the summary without changing the status
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {
            ATTR_ITEM: item["uid"],
            ATTR_RENAME: "other summary",
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Verify item is changed and still marked as completed
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "other summary"
    assert item["status"] == "completed"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"