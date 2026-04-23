async def _websocket_forward(
    ws_from: web.WebSocketResponse | ClientWebSocketResponse,
    ws_to: web.WebSocketResponse | ClientWebSocketResponse,
) -> None:
    """Handle websocket message directly."""
    try:
        async for msg in ws_from:
            if msg.type is aiohttp.WSMsgType.TEXT:
                await ws_to.send_str(msg.data)
            elif msg.type is aiohttp.WSMsgType.BINARY:
                await ws_to.send_bytes(msg.data)
            elif msg.type is aiohttp.WSMsgType.PING:
                await ws_to.ping(msg.data)
            elif msg.type is aiohttp.WSMsgType.PONG:
                await ws_to.pong(msg.data)
            elif ws_to.closed:
                await ws_to.close(code=ws_to.close_code, message=msg.extra)  # type: ignore[arg-type]
    except RuntimeError:
        _LOGGER.debug("Ingress Websocket runtime error")
    except ConnectionResetError:
        _LOGGER.debug("Ingress Websocket Connection Reset")