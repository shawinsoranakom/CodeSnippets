def test_override_multiple_attributes(self) -> None:
        """Test overriding multiple attributes at once."""

        @tool
        def test_tool(x: int) -> str:
            """A test tool."""
            return f"Result: {x}"

        @tool
        def another_tool(y: str) -> str:
            """Another test tool."""
            return f"Output: {y}"

        original_call = ToolCall(name="test_tool", args={"x": 5}, id="1", type="tool_call")
        modified_call = ToolCall(
            name="another_tool",
            args={"y": "hello"},
            id="2",
            type="tool_call",
        )

        original_request = ToolCallRequest(
            tool_call=original_call,
            tool=test_tool,
            state={"count": 1},
            runtime=Mock(),
        )

        new_request = original_request.override(
            tool_call=modified_call,
            tool=another_tool,
            state={"count": 2},
        )

        assert new_request.tool_call["name"] == "another_tool"
        assert new_request.tool is not None
        assert new_request.tool.name == "another_tool"
        assert new_request.state == {"count": 2}
        # Original unchanged
        assert original_request.tool_call["name"] == "test_tool"
        assert original_request.tool is not None
        assert original_request.tool.name == "test_tool"
        assert original_request.state == {"count": 1}