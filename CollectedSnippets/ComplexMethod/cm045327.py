async def test_static_stream_workbench_call_tool_stream() -> None:
    """Test call_tool_stream with streaming tools and regular tools."""

    def regular_tool_func(x: Annotated[int, "The number to double."]) -> int:
        return x * 2

    regular_tool = FunctionTool(
        regular_tool_func,
        name="regular_tool",
        description="A regular tool that doubles a number.",
        global_imports=[ImportFromModule(module="typing_extensions", imports=["Annotated"])],
    )

    stream_tool = StreamTool()
    stream_tool_with_error = StreamToolWithError()

    async with StaticStreamWorkbench(tools=[regular_tool, stream_tool, stream_tool_with_error]) as workbench:
        # Test streaming tool
        results: list[StreamItem | StreamResult | ToolResult] = []
        async for result in workbench.call_tool_stream("test_stream_tool", {"count": 3}):
            results.append(result)

        # Should get 3 intermediate results and 1 final result
        assert len(results) == 4

        # Check intermediate results (StreamItem objects)
        for i, result in enumerate(results[:3]):
            assert isinstance(result, StreamItem)
            assert result.current == i + 1

        # Check final result (ToolResult)
        final_result = results[-1]
        assert isinstance(final_result, ToolResult)
        assert final_result.name == "test_stream_tool"
        assert final_result.is_error is False
        assert final_result.result[0].type == "TextResultContent"
        assert "final_count" in final_result.result[0].content

        # Test regular (non-streaming) tool
        results_regular: list[ToolResult] = []
        async for result in workbench.call_tool_stream("regular_tool", {"x": 5}):
            results_regular.append(result)  # type: ignore

        # Should get only 1 result for non-streaming tool
        assert len(results_regular) == 1
        final_result = results_regular[0]
        assert final_result.name == "regular_tool"
        assert final_result.is_error is False
        assert final_result.result[0].content == "10"

        # Test streaming tool with error
        results_error: list[StreamItem | ToolResult] = []
        async for result in workbench.call_tool_stream("test_stream_tool_error", {"count": 3}):
            results_error.append(result)  # type: ignore

        # Should get 1 intermediate result and 1 error result
        assert len(results_error) == 2

        # Check intermediate result
        intermediate_result = results_error[0]
        assert isinstance(intermediate_result, StreamItem)
        assert intermediate_result.current == 1

        # Check error result
        error_result = results_error[1]
        assert isinstance(error_result, ToolResult)
        assert error_result.name == "test_stream_tool_error"
        assert error_result.is_error is True
        result_content = error_result.result[0]
        assert isinstance(result_content, TextResultContent)
        assert "Stream tool error" in result_content.content

        # Test tool not found
        results_not_found: list[ToolResult] = []
        async for result in workbench.call_tool_stream("nonexistent_tool", {"x": 5}):
            results_not_found.append(result)  # type: ignore

        assert len(results_not_found) == 1
        error_result = results_not_found[0]
        assert error_result.name == "nonexistent_tool"
        assert error_result.is_error is True
        result_content = error_result.result[0]
        assert isinstance(result_content, TextResultContent)
        assert "Tool nonexistent_tool not found" in result_content.content

        # Test with no arguments
        results_no_args: list[StreamItem | StreamResult | ToolResult] = []
        async for result in workbench.call_tool_stream("test_stream_tool", {"count": 1}):
            results_no_args.append(result)  # type: ignore

        assert len(results_no_args) == 2  # 1 intermediate + 1 final

        # Test with None arguments
        results_none: list[ToolResult] = []
        async for result in workbench.call_tool_stream("regular_tool", None):
            results_none.append(result)  # type: ignore

        # Should still work but may get error due to missing required argument
        assert len(results_none) == 1
        result = results_none[0]
        assert result.name == "regular_tool"
        # This should error because x is required
        assert result.is_error is True