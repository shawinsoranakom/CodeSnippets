async def test_add_item(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_integration: None,
    ws_get_items: Callable[[], Awaitable[dict[str, str]]],
    item_data: dict[str, Any],
    expected_item_data: dict[str, Any],
) -> None:
    """Test adding a todo item."""

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "0"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "replace batteries", **item_data},
        target={ATTR_ENTITY_ID: TEST_ENTITY},
        blocking=True,
    )

    items = await ws_get_items()
    assert len(items) == 1
    item_data = items[0]
    assert "uid" in item_data
    del item_data["uid"]
    assert item_data == expected_item_data

    state = hass.states.get(TEST_ENTITY)
    assert state
    assert state.state == "1"