async def test_rename(
    hass: HomeAssistant,
    setup_integration: None,
    ws_get_items: Callable[[], Awaitable[dict[str, str]]],
) -> None:
    """Test renaming a todo item."""

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

    # Rename item
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: item["uid"], ATTR_RENAME: "water"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    # Verify item has been renamed
    items = await ws_get_items()
    assert len(items) == 1
    item = items[0]
    assert item["summary"] == "water"
    assert item["status"] == "needs_action"

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"