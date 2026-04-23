async def test_update_todo_list_item(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    mock_http_response: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for updating a To-do Item."""

    assert await integration_setup()

    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == "1"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "some-task-id", ATTR_RENAME: "Soda", ATTR_STATUS: "completed"},
        target={ATTR_ENTITY_ID: "todo.my_tasks"},
        blocking=True,
    )
    assert len(mock_http_response.call_args_list) == 4
    call = mock_http_response.call_args_list[2]
    assert call
    assert call.args == snapshot
    assert call.kwargs.get("body") == snapshot