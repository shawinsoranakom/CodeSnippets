async def _collect_streamed_tool_call(
    stream: openai.AsyncStream,
    *,
    expected_finish_reason: str = "tool_calls",
) -> StreamedToolCallResult:
    result = StreamedToolCallResult()

    async for chunk in stream:
        if chunk.choices[0].finish_reason:
            result.finish_reason_count += 1
            result.finish_reason = chunk.choices[0].finish_reason
            assert chunk.choices[0].finish_reason == expected_finish_reason

        if chunk.choices[0].delta.role:
            assert not result.role_name or result.role_name == "assistant"
            result.role_name = "assistant"

        streamed_tool_calls = chunk.choices[0].delta.tool_calls
        if streamed_tool_calls and len(streamed_tool_calls) > 0:
            assert len(streamed_tool_calls) == 1
            tool_call = streamed_tool_calls[0]

            if tool_call.id:
                assert not result.tool_call_id
                result.tool_call_id = tool_call.id

            if tool_call.function:
                if tool_call.function.name:
                    assert result.function_name is None
                    result.function_name = tool_call.function.name
                if tool_call.function.arguments:
                    result.function_args_str += tool_call.function.arguments

    return result