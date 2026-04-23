async def _collect_streamed_parallel_tool_calls(
    stream: openai.AsyncStream,
) -> StreamedParallelToolCallResult:
    r"""Consume a streaming response and collect parallel tool calls."""
    result = StreamedParallelToolCallResult()
    tool_call_idx: int = -1

    async for chunk in stream:
        if chunk.choices[0].finish_reason:
            result.finish_reason_count += 1
            assert chunk.choices[0].finish_reason == "tool_calls"

        if chunk.choices[0].delta.role:
            assert not result.role_name or result.role_name == "assistant"
            result.role_name = "assistant"

        streamed_tool_calls = chunk.choices[0].delta.tool_calls
        if streamed_tool_calls and len(streamed_tool_calls) > 0:
            assert len(streamed_tool_calls) == 1
            tool_call = streamed_tool_calls[0]

            if tool_call.index != tool_call_idx:
                tool_call_idx = tool_call.index
                result.function_args_strs.append("")
                result.tool_call_ids.append("")

            if tool_call.id:
                result.tool_call_ids[tool_call.index] = tool_call.id

            if tool_call.function:
                if tool_call.function.name:
                    result.function_names.append(tool_call.function.name)
                if tool_call.function.arguments:
                    result.function_args_strs[tool_call.index] += (
                        tool_call.function.arguments
                    )

    return result