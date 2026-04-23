def test_filter_multiple_injected_args() -> None:
    """Test filtering multiple injected arguments from callback inputs."""

    @tool
    def complex_tool(
        query: str,
        limit: int,
        state: Annotated[dict, InjectedToolArg()],
        context: Annotated[str, InjectedToolArg()],
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """Complex tool with multiple injected args.

        Args:
            query: The search query.
            limit: Maximum number of results.
            state: Injected state.
            context: Injected context.
            run_manager: The callback manager.
        """
        return f"Query: {query}, Limit: {limit}"

    handler = CallbackHandlerWithInputCapture(captured_inputs=[])
    result = complex_tool.invoke(
        {
            "query": "test",
            "limit": 10,
            "state": {"foo": "bar"},
            "context": "some context",
        },
        config={"callbacks": [handler]},
    )

    assert result == "Query: test, Limit: 10"
    assert handler.tool_starts == 1
    assert len(handler.captured_inputs) == 1

    # Verify that only non-injected args remain
    captured = handler.captured_inputs[0]
    assert captured is not None
    assert captured == {"query": "test", "limit": 10}
    assert "state" not in captured
    assert "context" not in captured
    assert "run_manager" not in captured