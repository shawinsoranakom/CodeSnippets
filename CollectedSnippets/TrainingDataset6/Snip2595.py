def test_two_scopes() -> None:
    global_context.set({})
    global_state = global_context.get()
    with client.websocket_connect("/two-scopes") as websocket:
        data = websocket.receive_json()
    assert data["func_is_open"] is True
    assert data["req_is_open"] is True
    assert global_state["session_closed"] is True