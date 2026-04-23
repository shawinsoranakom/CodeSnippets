async def test_filter_injected_args_async() -> None:
    """Test that injected args are filtered in async tool execution."""

    @tool
    async def async_search_tool(
        query: str,
        state: Annotated[dict, InjectedToolArg()],
    ) -> str:
        """Async search with injected state.

        Args:
            query: The search query.
            state: Injected state context.
        """
        return f"Async results for: {query}"

    handler = CallbackHandlerWithInputCapture(captured_inputs=[])
    result = await async_search_tool.ainvoke(
        {"query": "async test", "state": {"user_id": 456}},
        config={"callbacks": [handler]},
    )

    assert result == "Async results for: async test"
    assert handler.tool_starts == 1
    assert len(handler.captured_inputs) == 1

    # Verify filtering in async execution
    captured = handler.captured_inputs[0]
    assert captured is not None
    assert "query" in captured
    assert "state" not in captured
    assert captured["query"] == "async test"