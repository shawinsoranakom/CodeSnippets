async def websocket_validation_handler(
    websocket: WebSocket, exc: WebSocketRequestValidationError
):
    captured_exception.capture(exc)
    raise exc