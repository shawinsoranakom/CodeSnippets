async def test_session_health_check_and_recovery(mcp_server_params, process_tracker):
    """Test that unhealthy sessions are properly detected and recreated."""
    process, initial_count = process_tracker

    session_manager = MCPSessionManager()

    try:
        # Create a session
        session1 = await session_manager.get_session("health_test", mcp_server_params, "stdio")
        tools_response = await wait_tools(session1)
        assert len(tools_response.tools) > 0

        # Simulate session becoming unhealthy by accessing internal state
        # This is a bit of a hack but necessary for testing
        server_key = session_manager._get_server_key(mcp_server_params, "stdio")
        if hasattr(session_manager, "sessions_by_server"):
            # For the fixed version
            sessions = session_manager.sessions_by_server.get(server_key, {})
            if sessions:
                session_id = next(iter(sessions.keys()))
                session_info = sessions[session_id]
                if "task" in session_info:
                    task = session_info["task"]
                    if not task.done():
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task
        elif hasattr(session_manager, "sessions"):
            # For the original version
            for session_info in session_manager.sessions.values():
                if "task" in session_info:
                    task = session_info["task"]
                    if not task.done():
                        task.cancel()
                        with contextlib.suppress(asyncio.CancelledError):
                            await task

        # Wait a bit for the task to be cancelled
        await asyncio.sleep(1)

        # Try to get a session again - should create a new healthy one
        session2 = await session_manager.get_session("health_test_2", mcp_server_params, "stdio")
        tools_response = await wait_tools(session2)
        assert len(tools_response.tools) > 0

    finally:
        await session_manager.cleanup_all()
        await wait_no_children(process, max_wait=10, target=initial_count)
        await asyncio.sleep(2)