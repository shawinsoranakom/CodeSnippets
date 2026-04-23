async def test_create_todo_list_item(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    mock_http_response: Mock,
    item_data: dict[str, Any],
    snapshot: SnapshotAssertion,
) -> None:
    """Test for creating a To-do Item."""

    assert await integration_setup()

    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == "0"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.ADD_ITEM,
        {ATTR_ITEM: "Soda", **item_data},
        target={ATTR_ENTITY_ID: "todo.my_tasks"},
        blocking=True,
    )
    assert len(mock_http_response.call_args_list) == 4
    call = mock_http_response.call_args_list[2]
    assert call
    assert call.args == snapshot
    assert call.kwargs.get("body") == snapshot