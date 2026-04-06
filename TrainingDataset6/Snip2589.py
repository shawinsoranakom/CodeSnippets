async def get_stream_session(
    websocket: WebSocket,
    function_session: SessionFuncDep,
    request_session: SessionRequestDep,
) -> Any:
    await websocket.accept()
    await websocket.send_json(
        {"func_is_open": function_session.open, "req_is_open": request_session.open}
    )