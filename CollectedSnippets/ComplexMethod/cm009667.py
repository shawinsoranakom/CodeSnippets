def test_filter_injected_args_from_callbacks() -> None:
    """Test that injected tool arguments are filtered from callback inputs."""

    @tool
    def search_tool(
        query: str,
        state: Annotated[dict, InjectedToolArg()],
    ) -> str:
        """Search with injected state.

        Args:
            query: The search query.
            state: Injected state context.
        """
        return f"Results for: {query}"

    handler = CallbackHandlerWithInputCapture(captured_inputs=[])
    result = search_tool.invoke(
        {"query": "test query", "state": {"user_id": 123}},
        config={"callbacks": [handler]},
    )

    assert result == "Results for: test query"
    assert handler.tool_starts == 1
    assert len(handler.captured_inputs) == 1

    # Verify that injected 'state' arg is filtered out
    captured = handler.captured_inputs[0]
    assert captured is not None
    assert "query" in captured
    assert "state" not in captured
    assert captured["query"] == "test query"