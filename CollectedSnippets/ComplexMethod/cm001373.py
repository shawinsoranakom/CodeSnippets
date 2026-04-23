async def test_conversation_with_tool_history(self, anthropic_provider, model_name):
        """Build conversation history with tool calls, then make another call.
        Verifies Anthropic message format stays correct across operations."""
        # First call returns a tool use
        tool_block = _make_anthropic_tool_use("tool_1", "web_search", {"query": "test"})
        anthropic_provider._client.messages.create = AsyncMock(
            return_value=_make_anthropic_response(
                "Searching", tool_use_blocks=[tool_block]
            )
        )

        r1 = await anthropic_provider.create_chat_completion(
            model_prompt=[ChatMessage.user("search test")],
            model_name=model_name,
            functions=[SEARCH_FUNCTION],
        )

        # Build history for second call
        history = [
            ChatMessage.user("search test"),
            r1.response,
            ToolResultMessage(tool_call_id="tool_1", content="Found results"),
            ChatMessage.user("summarize"),
        ]

        # Verify message prep handles this history correctly
        anthropic_msgs, kwargs = anthropic_provider._get_chat_completion_args(
            prompt_messages=history, functions=[SEARCH_FUNCTION]
        )

        # Should have: user, assistant (with tool_use), user (with tool_result), user
        roles = [m["role"] for m in anthropic_msgs]
        assert "assistant" in roles
        assert "user" in roles

        # Assistant message should have tool_use blocks
        assistant_msg = next(m for m in anthropic_msgs if m["role"] == "assistant")
        assert isinstance(assistant_msg["content"], list)
        tool_use_blocks = [
            b for b in assistant_msg["content"] if b["type"] == "tool_use"
        ]
        assert len(tool_use_blocks) == 1
        assert tool_use_blocks[0]["name"] == "web_search"