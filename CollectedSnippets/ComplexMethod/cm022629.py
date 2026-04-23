async def test_partial_update_status(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    mock_http_response: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for partial update with status only."""

    assert await integration_setup()

    state = hass.states.get("todo.my_tasks")
    assert state
    assert state.state == "1"

    await hass.services.async_call(
        TODO_DOMAIN,
        TodoServices.UPDATE_ITEM,
        {ATTR_ITEM: "some-task-id", ATTR_STATUS: "needs_action"},
        target={ATTR_ENTITY_ID: "todo.my_tasks"},
        blocking=True,
    )
    assert len(mock_http_response.call_args_list) == 4
    call = mock_http_response.call_args_list[2]
    assert call
    assert call.args == snapshot
    assert call.kwargs.get("body") == snapshot