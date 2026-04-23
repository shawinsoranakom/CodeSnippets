async def test_add_todo_list_item(
    hass: HomeAssistant,
    setup_integration: None,
    ourgroceries: AsyncMock,
) -> None:
    """Test for adding an item."""

    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "0"

    ourgroceries.add_item_to_list = AsyncMock()
    # Fake API response when state is refreshed after create
    _mock_version_id(ourgroceries, 2)
    ourgroceries.get_list_items.return_value = items_to_shopping_list(
        [{"id": "12345", "name": "Soda"}],
        version_id="2",
    )

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "Soda"},
        target={ATTR_ENTITY_ID: "todo.test_list"},
        blocking=True,
    )

    args = ourgroceries.add_item_to_list.call_args
    assert args
    assert args.args == ("test_list", "Soda")
    assert args.kwargs.get("auto_category") is True

    # Verify state is refreshed
    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "1"