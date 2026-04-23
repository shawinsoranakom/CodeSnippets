async def test_add_todo_list_item(
    hass: HomeAssistant,
    setup_integration: None,
    api: AsyncMock,
    item_data: dict[str, Any],
    tasks_after_update: list[Task],
    add_kwargs: dict[str, Any],
    expected_item: dict[str, Any],
) -> None:
    """Test for adding a To-do Item."""

    state = hass.states.get("todo.name")
    assert state
    assert state.state == "0"

    api.add_task = AsyncMock()
    # Fake API response when state is refreshed after create
    api.get_tasks.side_effect = make_api_response(tasks_after_update)

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "Soda", **item_data},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
    )

    args = api.add_task.call_args
    assert args
    assert args.kwargs == {"project_id": PROJECT_ID, "content": "Soda", **add_kwargs}

    # Verify state is refreshed
    state = hass.states.get("todo.name")
    assert state
    assert state.state == "1"

    result = await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.GET_ITEMS,
        {},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
        return_response=True,
    )
    assert result == {"todo.name": {"items": [expected_item]}}