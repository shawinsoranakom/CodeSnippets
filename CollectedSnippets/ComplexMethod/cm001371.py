async def test_conversation_history_with_tool_calls_serializes_correctly(
        self, openai_provider, model_name
    ):
        """Simulate building up a conversation with tool calls in history.

        This is the EXACT scenario that caused the GPT-5.2 400 error:
        tool_calls arguments must be JSON strings when sent back to the API.
        """
        # First call
        tc = _make_openai_tool_call("call_1", "web_search", {"query": "AI news"})
        openai_provider._client.chat.completions.create = AsyncMock(
            return_value=_make_openai_completion("Searching", tool_calls=[tc])
        )

        r1 = await openai_provider.create_chat_completion(
            model_prompt=[ChatMessage.user("search for AI news")],
            model_name=model_name,
            functions=[SEARCH_FUNCTION],
        )

        # Build conversation history including the tool call and its result
        history = [
            ChatMessage.user("search for AI news"),
            r1.response,  # AssistantChatMessage with tool_calls
            ToolResultMessage(tool_call_id="call_1", content="Found 10 results"),
            ChatMessage.user("summarize the results"),
        ]

        # Second call with history — this is where the bug occurred
        openai_provider._client.chat.completions.create = AsyncMock(
            return_value=_make_openai_completion("Here is a summary of AI news...")
        )

        # This call must prep messages correctly: tool_calls args as JSON strings
        prepped_msgs, kwargs, _ = openai_provider._get_chat_completion_args(
            prompt_messages=history,
            model=model_name,
        )

        # Verify the assistant message's tool_calls have string arguments
        assistant_msg = next(m for m in prepped_msgs if m["role"] == "assistant")
        for tc_dict in assistant_msg.get("tool_calls", []):
            args = tc_dict["function"]["arguments"]
            assert isinstance(args, str), (
                f"Model {model_name}: tool_calls arguments must be JSON string, "
                f"got {type(args).__name__}: {args}"
            )
            # Must be valid JSON
            parsed = json.loads(args)
            assert isinstance(parsed, dict)

        # The tool result message must be present
        tool_msg = next(m for m in prepped_msgs if m.get("role") == "tool")
        assert tool_msg["tool_call_id"] == "call_1"