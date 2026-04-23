def test_sub() -> None:
    global_context.set({})
    global_state = global_context.get()
    with client.websocket_connect("/sub") as websocket:
        data = websocket.receive_json()
    assert data["named_session_open"] is True
    assert data["session_open"] is True
    assert global_state["session_closed"] is True
    assert global_state["named_session_closed"] is True