async def test_remove_todo_item(
    hass: HomeAssistant,
    setup_integration: None,
    ourgroceries: AsyncMock,
) -> None:
    """Test for removing an item."""

    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "2"

    ourgroceries.remove_item_from_list = AsyncMock()
    # Fake API response when state is refreshed after remove
    _mock_version_id(ourgroceries, 2)
    ourgroceries.get_list_items.return_value = items_to_shopping_list([])

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {ATTR_ITEM: ["12345", "54321"]},
        target={ATTR_ENTITY_ID: "todo.test_list"},
        blocking=True,
    )
    assert ourgroceries.remove_item_from_list.call_count == 2
    args = ourgroceries.remove_item_from_list.call_args_list
    assert args[0].args == ("test_list", "12345")
    assert args[1].args == ("test_list", "54321")

    await async_update_entity(hass, "todo.test_list")
    state = hass.states.get("todo.test_list")
    assert state
    assert state.state == "0"