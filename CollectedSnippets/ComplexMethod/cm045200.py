async def test_run_actor_all_command_types_exception_handling() -> None:
    """Test _run_actor exception handling for all command types (lines 232-233, 238-239, 244-245, 250-251, 256-263)."""
    actor = McpSessionActor(StdioServerParams(command="echo", args=["test"]))

    # Create a mock session that will raise exceptions for all command types
    @asynccontextmanager
    async def mock_failing_session(
        server_params: Any,
        sampling_callback: Any = None,
        elicitation_callback: Any = None,
        list_roots_callback: Any = None,
    ) -> AsyncGenerator[MagicMock, None]:
        mock_session = MagicMock()
        mock_session.initialize = AsyncMock(
            return_value=mcp_types.InitializeResult(
                protocolVersion="1.0",
                capabilities=mcp_types.ServerCapabilities(),
                serverInfo=mcp_types.Implementation(name="test", version="1.0"),
            )
        )
        # Make all session methods raise exceptions
        mock_session.call_tool = MagicMock(side_effect=Exception("call_tool error"))
        mock_session.read_resource = MagicMock(side_effect=Exception("read_resource error"))
        mock_session.get_prompt = MagicMock(side_effect=Exception("get_prompt error"))
        mock_session.list_tools = MagicMock(side_effect=Exception("list_tools error"))
        mock_session.list_prompts = MagicMock(side_effect=Exception("list_prompts error"))
        mock_session.list_resources = MagicMock(side_effect=Exception("list_resources error"))
        mock_session.list_resource_templates = MagicMock(side_effect=Exception("list_resource_templates error"))
        yield mock_session

    with patch("autogen_ext.tools.mcp._actor.create_mcp_server_session", mock_failing_session):  # type: ignore[reportPrivateUsage]
        # Start the actor task
        actor._active = True  # type: ignore[reportPrivateUsage]
        actor_task = asyncio.create_task(actor._run_actor())  # type: ignore[reportPrivateUsage]

        try:
            # Give it a moment to initialize
            await asyncio.sleep(0.05)

            # Test all command types that can raise exceptions (including line 212)
            commands_to_test: list[dict[str, Any]] = [
                {"type": "call_tool", "name": "test_tool", "args": {}},
                {"type": "read_resource", "uri": "test://resource"},
                {"type": "get_prompt", "name": "test_prompt", "args": {}},
                {"type": "list_tools"},
                {"type": "list_prompts"},
                {"type": "list_resources"},
                {"type": "list_resource_templates"},  # This covers line 212
            ]

            futures: list[asyncio.Future[Any]] = []
            for cmd in commands_to_test:
                future: asyncio.Future[Any] = asyncio.Future()
                cmd["future"] = future
                await actor._command_queue.put(cmd)  # type: ignore[reportPrivateUsage]
                futures.append(future)

            # Wait a bit for commands to be processed
            await asyncio.sleep(0.1)

            # Send shutdown command
            shutdown_future: asyncio.Future[Any] = asyncio.Future()
            await actor._command_queue.put({"type": "shutdown", "future": shutdown_future})  # type: ignore[reportPrivateUsage]

            # Wait for actor to finish
            try:
                await asyncio.wait_for(actor_task, timeout=1.0)
            except asyncio.TimeoutError:
                pass  # Expected if task doesn't finish properly

            # Verify that all futures were set with exceptions
            for i, future in enumerate(futures):
                assert future.done(), f"Future {i} was not completed"
                assert future.exception() is not None, f"Future {i} should have an exception"

        finally:
            # Ensure the task is cancelled and cleaned up
            if not actor_task.done():
                actor_task.cancel()
                try:
                    await actor_task
                except asyncio.CancelledError:
                    pass