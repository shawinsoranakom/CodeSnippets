async def test_update_todo_item_status(
    hass: HomeAssistant,
    setup_integration: None,
    api: AsyncMock,
) -> None:
    """Test for updating a To-do Item that changes the status."""

    state = hass.states.get("todo.name")
    assert state
    assert state.state == "1"

    api.complete_task = AsyncMock()
    api.uncomplete_task = AsyncMock()

    # Fake API response when state is refreshed after complete
    api.get_tasks.side_effect = make_api_response(
        [
            make_api_task(
                id="task-id-1", content="Soda", completed_at="2021-10-01T00:00:00"
            )
        ]
    )

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "task-id-1", ATTR_STATUS: "completed"},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
    )
    assert api.complete_task.called
    args = api.complete_task.call_args
    assert args
    assert args.kwargs.get("task_id") == "task-id-1"
    assert not api.uncomplete_task.called

    # Verify state is refreshed
    state = hass.states.get("todo.name")
    assert state
    assert state.state == "0"

    # Fake API response when state is refreshed after reopening task
    api.get_tasks.side_effect = make_api_response(
        [make_api_task(id="task-id-1", content="Soda", completed_at=None)]
    )

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "task-id-1", ATTR_STATUS: "needs_action"},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
    )
    assert api.uncomplete_task.called
    args = api.uncomplete_task.call_args
    assert args
    assert args.kwargs.get("task_id") == "task-id-1"

    # Verify state is refreshed
    state = hass.states.get("todo.name")
    assert state
    assert state.state == "1"