async def mcp_websocket(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint - looks up server params from server-side storage"""
    # Look up pre-registered server params (one-time use)
    server_params = pending_session_params.pop(session_id, None)
    if server_params is None:
        await websocket.close(code=4004, reason="Unknown or expired session")
        return

    await websocket.accept()
    logger.info(f"MCP WebSocket connection established for session {session_id}")

    bridge = None

    try:
        # Create bridge and run MCP session
        bridge = MCPWebSocketBridge(websocket, session_id)
        await create_mcp_session(bridge, server_params, session_id)

    except WebSocketDisconnect:
        logger.info(f"MCP WebSocket session {session_id} disconnected normally")
    except Exception as e:
        real_error = extract_real_error(e)

        if is_websocket_disconnect(e):
            logger.info(f"MCP WebSocket session {session_id} disconnected (wrapped)")
        else:
            logger.error(f"MCP WebSocket error for session {session_id}: {real_error}")

            if bridge and not is_websocket_disconnect(e):
                try:
                    await bridge.send_message(
                        {
                            "type": "error",
                            "error": f"Connection error: {real_error}",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                except Exception:
                    pass
    finally:
        # Cleanup
        if session_id in active_sessions:
            session_info = active_sessions.pop(session_id, None)
            if session_info:
                duration = datetime.now(timezone.utc) - session_info["created_at"]
                logger.info(f"MCP session {session_id} ended after {duration.total_seconds():.2f} seconds")

        if bridge:
            bridge.stop()