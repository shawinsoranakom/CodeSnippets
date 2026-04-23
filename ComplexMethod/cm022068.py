async def test_remove_item(
    hass: HomeAssistant,
    sl_setup: None,
    ws_get_items: WsGetItemsType,
) -> None:
    """Test removing a todo item."""
    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "soda"},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )
    items = await ws_get_items()
    assert len(items) == 1
    assert items[0]["summary"] == "soda"
    assert items[0]["status"] == "needs_action"
    assert "uid" in items[0]

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {
            ATTR_ITEM: [items[0]["uid"]],
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    assert len(items) == 0

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"