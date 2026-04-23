async def get_named_function_scope(
    websocket: WebSocket, sessions: NamedSessionsFuncDep
) -> Any:
    await websocket.accept()
    await websocket.send_json(
        {"named_session_open": sessions[0].open, "session_open": sessions[1].open}
    )