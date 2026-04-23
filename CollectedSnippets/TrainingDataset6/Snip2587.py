async def function_scope(websocket: WebSocket, session: SessionFuncDep) -> Any:
    await websocket.accept()
    await websocket.send_json({"is_open": session.open})