def test_named_function_scope() -> None:
    global_context.set({})
    global_state = global_context.get()
    with client.websocket_connect("/named-function-scope") as websocket:
        data = websocket.receive_json()
    assert data["named_session_open"] is True
    assert data["session_open"] is True
    assert global_state["session_closed"] is True
    assert global_state["named_func_session_closed"] is True