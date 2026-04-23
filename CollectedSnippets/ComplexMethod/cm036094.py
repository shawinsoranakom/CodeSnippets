async def _collect_streamed_content(
    stream: openai.AsyncStream,
    *,
    expected_finish_reason: str | None = None,
    no_tool_calls: bool = True,
) -> StreamedContentResult:
    r"""Consume a streaming response and collect text content."""
    result = StreamedContentResult()

    async for chunk in stream:
        delta = chunk.choices[0].delta

        if delta.role:
            assert not result.role_sent
            assert delta.role == "assistant"
            result.role_sent = True

        if delta.content:
            result.chunks.append(delta.content)

        if chunk.choices[0].finish_reason is not None:
            result.finish_reason_count += 1
            result.finish_reason = chunk.choices[0].finish_reason
            if expected_finish_reason is not None:
                assert result.finish_reason == expected_finish_reason

        if no_tool_calls:
            assert not delta.tool_calls or len(delta.tool_calls) == 0

    return result