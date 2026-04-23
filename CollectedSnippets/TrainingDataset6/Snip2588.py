async def request_scope(websocket: WebSocket, session: SessionRequestDep) -> Any:
    await websocket.accept()
    await websocket.send_json({"is_open": session.open})