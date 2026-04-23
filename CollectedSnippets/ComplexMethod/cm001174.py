async def websocket_router(
    websocket: WebSocket, manager: ConnectionManager = Depends(get_connection_manager)
):
    user_id = await authenticate_websocket(websocket)
    if not user_id:
        return
    await manager.connect_socket(websocket, user_id=user_id)

    # Track WebSocket connection
    update_websocket_connections(user_id, 1)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = WSMessage.model_validate_json(data)
            except pydantic.ValidationError as e:
                logger.error(
                    "Invalid WebSocket message from user #%s: %s",
                    user_id,
                    e,
                )
                await websocket.send_text(
                    WSMessage(
                        method=WSMethod.ERROR,
                        success=False,
                        error=("Invalid message format. Review the schema and retry"),
                    ).model_dump_json()
                )
                continue

            try:
                if message.method in _MSG_HANDLERS:
                    await _MSG_HANDLERS[message.method](
                        connection_manager=manager,
                        websocket=websocket,
                        user_id=user_id,
                        message=message,
                    )
                    continue
            except pydantic.ValidationError as e:
                logger.error(
                    "Validation error while handling '%s' for user #%s: %s",
                    message.method.value,
                    user_id,
                    e,
                )
                await websocket.send_text(
                    WSMessage(
                        method=WSMethod.ERROR,
                        success=False,
                        error="Invalid message data. Refer to the API schema",
                    ).model_dump_json()
                )
                continue
            except Exception as e:
                logger.error(
                    f"Error while handling '{message.method.value}' message "
                    f"for user #{user_id}: {e}"
                )
                continue

            if message.method == WSMethod.ERROR:
                logger.error(f"WebSocket Error message received: {message.data}")

            else:
                logger.warning(
                    f"Unknown WebSocket message type {message.method} received: "
                    f"{message.data}"
                )
                await websocket.send_text(
                    WSMessage(
                        method=WSMethod.ERROR,
                        success=False,
                        error="Message type is not processed by the server",
                    ).model_dump_json()
                )

    except WebSocketDisconnect:
        manager.disconnect_socket(websocket, user_id=user_id)
        logger.debug("WebSocket client disconnected")
    finally:
        update_websocket_connections(user_id, -1)