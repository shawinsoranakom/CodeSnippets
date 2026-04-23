def test_combines_reasoning_and_mcp_tool_call(self):
        """Test successful combination of reasoning message and MCP tool call."""
        item = ResponseFunctionToolCall(
            type="function_call",
            id=f"{MCP_PREFIX}tool_id",
            call_id="call_123",
            name="test_function",
            arguments='{"arg": "value"}',
        )
        messages = [{"role": "assistant", "reasoning": "I need to call this tool"}]

        result = _maybe_combine_reasoning_and_tool_call(item, messages)

        assert result is not None
        assert result["role"] == "assistant"
        assert result["reasoning"] == "I need to call this tool"
        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["function"]["name"] == "test_function"
        assert result["tool_calls"][0]["function"]["arguments"] == '{"arg": "value"}'
        assert result["tool_calls"][0]["type"] == "function"