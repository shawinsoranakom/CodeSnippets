async def test_compressed_output_keeps_tool_calls_and_ids(self):
        # Simulate compression that returns a summary + the most recent
        # assistant(tool_call) + tool(tool_result) intact.
        summary = {"role": "system", "content": "prior turns: user asked X"}
        assistant_with_tc = {
            "role": "assistant",
            "content": "calling tool",
            "tool_calls": [
                {
                    "id": "tc_abc",
                    "type": "function",
                    "function": {"name": "search", "arguments": '{"q":"y"}'},
                }
            ],
        }
        tool_result = {
            "role": "tool",
            "tool_call_id": "tc_abc",
            "content": "search result",
        }

        compress_result = CompressResult(
            messages=[summary, assistant_with_tc, tool_result],
            token_count=100,
            was_compacted=True,
            original_token_count=5000,
            messages_summarized=10,
            messages_dropped=0,
        )

        # Input: messages that should be compressed.
        input_messages = [
            ChatMessage(role="user", content="q1"),
            ChatMessage(
                role="assistant",
                content="calling tool",
                tool_calls=[
                    {
                        "id": "tc_abc",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": '{"q":"y"}',
                        },
                    }
                ],
            ),
            ChatMessage(
                role="tool",
                tool_call_id="tc_abc",
                content="search result",
            ),
        ]

        with patch(
            "backend.copilot.baseline.service.compress_context",
            new=AsyncMock(return_value=compress_result),
        ):
            compressed = await _compress_session_messages(
                input_messages, model="openrouter/anthropic/claude-opus-4"
            )

        # Summary, assistant(tool_calls), tool(tool_call_id).
        assert len(compressed) == 3
        # Assistant message must keep its tool_calls intact.
        assistant_msg = compressed[1]
        assert assistant_msg.role == "assistant"
        assert assistant_msg.tool_calls is not None
        assert len(assistant_msg.tool_calls) == 1
        assert assistant_msg.tool_calls[0]["id"] == "tc_abc"
        assert assistant_msg.tool_calls[0]["function"]["name"] == "search"
        # Tool-role message must keep tool_call_id for OpenAI linkage.
        tool_msg = compressed[2]
        assert tool_msg.role == "tool"
        assert tool_msg.tool_call_id == "tc_abc"
        assert tool_msg.content == "search result"