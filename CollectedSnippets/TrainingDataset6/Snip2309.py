async def websocket_endpoint_broken(websocket: WebSocket, session: BrokenSessionDep):
    await websocket.accept()
    for item in session:
        await websocket.send_text(f"{item}")