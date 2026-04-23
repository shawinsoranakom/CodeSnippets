def test_filter_injected_args_not_in_schema(
    tool_func: Callable[..., str], runtime_value: Any, description: str
) -> None:
    """Test filtering injected args that are in function signature but not in schema.

    This tests the case where an injected argument (like ToolRuntime) is in the
    function signature but is not present in the args_schema. The fix ensures
    we check _injected_args_keys from the function signature, not just the schema.

    Args:
        tool_func: The tool function with an injected arg.
        runtime_value: The value to pass for the runtime arg.
        description: Description of the injection style being tested.
    """
    # Create StructuredTool with explicit args_schema that excludes runtime
    custom_tool = StructuredTool.from_function(
        func=tool_func,
        name="custom_tool",
        description=f"Tool with {description} arg not in schema",
        args_schema=_ToolArgsSchemaNoRuntime,
    )

    # Verify _injected_args_keys contains 'runtime'
    assert "runtime" in custom_tool._injected_args_keys

    handler = CallbackHandlerWithInputCapture(captured_inputs=[])

    result = custom_tool.invoke(
        {
            "query": "test",
            "limit": 5,
            "runtime": runtime_value,
        },
        config={"callbacks": [handler]},
    )

    assert result == "Query: test, Limit: 5"
    assert handler.tool_starts == 1
    assert len(handler.captured_inputs) == 1

    # Verify that runtime is filtered out even though it's not in args_schema
    captured = handler.captured_inputs[0]
    assert captured is not None
    assert captured == {"query": "test", "limit": 5}
    assert "runtime" not in captured