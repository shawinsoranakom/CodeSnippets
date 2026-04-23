async def test_static_stream_workbench_inheritance() -> None:
    """Test that StaticStreamWorkbench inherits from both StaticWorkbench and StreamWorkbench."""
    stream_tool = StreamTool()

    async with StaticStreamWorkbench(tools=[stream_tool]) as workbench:
        # Test that it has regular workbench functionality
        tools = await workbench.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_stream_tool"

        # Test regular call_tool method
        result = await workbench.call_tool("test_stream_tool", {"count": 2})
        assert result.name == "test_stream_tool"
        assert result.is_error is False

        # Test streaming functionality exists
        assert hasattr(workbench, "call_tool_stream")
        results: list[StreamItem | StreamResult | ToolResult] = []
        async for result in workbench.call_tool_stream("test_stream_tool", {"count": 2}):
            results.append(result)  # type: ignore
        assert len(results) == 3