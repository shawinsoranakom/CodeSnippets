async def websocket_endpoint(websocket: WebSocket, item_id: int):
    await websocket.accept()  # pragma: no cover
    await websocket.send_text(f"Item: {item_id}")  # pragma: no cover
    await websocket.close()