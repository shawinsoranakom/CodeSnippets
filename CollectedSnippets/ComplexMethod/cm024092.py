async def test_update_todo_item_status(
    hass: HomeAssistant,
    setup_integration: None,
    ourgroceries: AsyncMock,
) -> None:
    """Test for updating the completion status of an item."""

    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "1"

    ourgroceries.toggle_item_crossed_off = AsyncMock()

    # Fake API response when state is refreshed after crossing off
    _mock_version_id(ourgroceries, 2)
    ourgroceries.get_list_items.return_value = items_to_shopping_list(
        [{"id": "12345", "name": "Soda", "crossedOffAt": 1699107501}]
    )

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "12345", ATTR_STATUS: "completed"},
        target={ATTR_ENTITY_ID: "todo.test_list"},
        blocking=True,
    )
    assert ourgroceries.toggle_item_crossed_off.called
    args = ourgroceries.toggle_item_crossed_off.call_args
    assert args
    assert args.args == ("test_list", "12345")
    assert args.kwargs.get("cross_off") is True

    # Verify state is refreshed
    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "0"

    # Fake API response when state is refreshed after reopen
    _mock_version_id(ourgroceries, 2)
    ourgroceries.get_list_items.return_value = items_to_shopping_list(
        [{"id": "12345", "name": "Soda"}]
    )

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "12345", ATTR_STATUS: "needs_action"},
        target={ATTR_ENTITY_ID: "todo.test_list"},
        blocking=True,
    )
    assert ourgroceries.toggle_item_crossed_off.called
    args = ourgroceries.toggle_item_crossed_off.call_args
    assert args
    assert args.args == ("test_list", "12345")
    assert args.kwargs.get("cross_off") is False

    # Verify state is refreshed
    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "1"