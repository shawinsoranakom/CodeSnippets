async def websocket_endpoint(websocket: WebSocket, session: SessionDep):
    await websocket.accept()
    for item in session:
        await websocket.send_text(f"{item}")