async def test_remove_todo_item(
    hass: HomeAssistant,
    setup_integration: None,
    api: AsyncMock,
) -> None:
    """Test for removing a To-do Item."""

    state = hass.states.get("todo.name")
    assert state
    assert state.state == "2"

    api.delete_task = AsyncMock()
    # Fake API response when state is refreshed after close
    api.get_tasks.side_effect = make_api_response([])

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.REMOVE_ITEM,
        {ATTR_ITEM: ["task-id-1", "task-id-2"]},
        target={ATTR_ENTITY_ID: "todo.name"},
        blocking=True,
    )
    assert api.delete_task.call_count == 2
    args = api.delete_task.call_args_list
    assert args[0].kwargs.get("task_id") == "task-id-1"
    assert args[1].kwargs.get("task_id") == "task-id-2"

    await async_update_entity(hass, "todo.name")
    state = hass.states.get("todo.name")
    assert state
    assert state.state == "0"