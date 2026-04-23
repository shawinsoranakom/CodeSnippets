def _merge_consecutive_assistant_messages(
        messages: list[ChatCompletionMessageParam],
    ) -> list[ChatCompletionMessageParam]:
        """Merge consecutive assistant messages into single messages.

        Long-running tool flows can create split assistant messages: one with
        text content and another with tool_calls. Anthropic's API requires
        tool_result blocks to reference a tool_use in the immediately preceding
        assistant message, so these splits cause 400 errors via OpenRouter.
        """
        if len(messages) < 2:
            return messages

        result: list[ChatCompletionMessageParam] = [messages[0]]
        for msg in messages[1:]:
            prev = result[-1]
            if prev.get("role") != "assistant" or msg.get("role") != "assistant":
                result.append(msg)
                continue

            prev = cast(ChatCompletionAssistantMessageParam, prev)
            curr = cast(ChatCompletionAssistantMessageParam, msg)

            curr_content = curr.get("content") or ""
            if curr_content:
                prev_content = prev.get("content") or ""
                prev["content"] = (
                    f"{prev_content}\n{curr_content}" if prev_content else curr_content
                )

            curr_tool_calls = curr.get("tool_calls")
            if curr_tool_calls:
                prev_tool_calls = prev.get("tool_calls")
                prev["tool_calls"] = (
                    list(prev_tool_calls) + list(curr_tool_calls)
                    if prev_tool_calls
                    else list(curr_tool_calls)
                )
        return result