async def test_move_todo_item(
    hass: HomeAssistant,
    setup_credentials: None,
    integration_setup: Callable[[], Awaitable[bool]],
    ws_get_items: Callable[[], Awaitable[dict[str, str]]],
    hass_ws_client: WebSocketGenerator,
    mock_http_response: Any,
    snapshot: SnapshotAssertion,
) -> None:
    """Test for re-ordering a To-do Item."""

    assert await integration_setup()

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == "3"

    items = await ws_get_items()
    assert items == snapshot

    # Move to second in the list
    client = await hass_ws_client()
    data = {
        "id": id,
        "type": "todo/item/move",
        "entity_id": ENTITY_ID,
        "uid": "some-task-id-3",
        "previous_uid": "some-task-id-1",
    }
    await client.send_json_auto_id(data)
    resp = await client.receive_json()
    assert resp.get("success")

    assert len(mock_http_response.call_args_list) == 4
    call = mock_http_response.call_args_list[2]
    assert call
    assert call.args == snapshot
    assert call.kwargs.get("body") == snapshot

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == "3"

    items = await ws_get_items()
    assert items == snapshot