def test_assistant_message_with_tool_calls(self, provider):
        tc = AssistantToolCall(
            id="tool_1",
            type="function",
            function=AssistantFunctionCall(name="search", arguments={"query": "test"}),
        )
        messages = [
            ChatMessage.user("Search"),
            AssistantChatMessage(content="Searching...", tool_calls=[tc]),
        ]
        anthropic_msgs, _ = provider._get_chat_completion_args(prompt_messages=messages)
        assistant_msg = anthropic_msgs[1]
        assert assistant_msg["role"] == "assistant"
        # Should have content blocks
        assert isinstance(assistant_msg["content"], list)
        # First block is text, second is tool_use
        text_blocks = [b for b in assistant_msg["content"] if b["type"] == "text"]
        tool_blocks = [b for b in assistant_msg["content"] if b["type"] == "tool_use"]
        assert len(text_blocks) == 1
        assert len(tool_blocks) == 1
        assert tool_blocks[0]["name"] == "search"
        assert tool_blocks[0]["input"] == {"query": "test"}