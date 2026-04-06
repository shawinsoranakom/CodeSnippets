def test_function_scope() -> None:
    global_context.set({})
    global_state = global_context.get()
    with client.websocket_connect("/function-scope") as websocket:
        data = websocket.receive_json()
    assert data["is_open"] is True
    assert global_state["session_closed"] is True