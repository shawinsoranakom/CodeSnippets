async def test_bulk_remove(
    hass: HomeAssistant,
    sl_setup: None,
    ws_get_items: WsGetItemsType,
) -> None:
    """Test removing a todo item."""

    for _i in range(5):
        await hass.services.async_call(
            TODO_DOMAIN,
            TodoServices.ADD_ITEM,
            {
                ATTR_ITEM: "soda",
            },
            target={ATTR_ENTITY_ID: TEST_ENTITY},
            blocking=True,
        )

    items = await ws_get_items()
    assert len(items) == 5
    uids = [item["uid"] for item in items]

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "5"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {
            ATTR_ITEM: uids,
        },
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    assert len(items) == 0

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"