async def test_single_tool_call_then_text():
    """LLM makes one tool call, then responds with text on second round."""
    call_count = 0

    async def llm_call(
        messages: list[dict[str, Any]], tools: Sequence[Any]
    ) -> LLMLoopResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_response(
                tool_calls=[
                    LLMToolCall(
                        id="tc_1", name="get_weather", arguments='{"city":"NYC"}'
                    )
                ]
            )
        return _make_response(text="It's sunny in NYC")

    async def execute_tool(
        tool_call: LLMToolCall, tools: Sequence[Any]
    ) -> ToolCallResult:
        return ToolCallResult(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            content='{"temp": 72}',
        )

    def update_conversation(
        messages: list[dict[str, Any]],
        response: LLMLoopResponse,
        tool_results: list[ToolCallResult] | None = None,
    ) -> None:
        messages.append({"role": "assistant", "content": response.response_text})
        if tool_results:
            for tr in tool_results:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.tool_call_id,
                        "content": tr.content,
                    }
                )

    msgs: list[dict[str, Any]] = [{"role": "user", "content": "Weather?"}]
    results: list[ToolCallLoopResult] = []
    async for r in tool_call_loop(
        messages=msgs,
        tools=TOOL_DEFS,
        llm_call=llm_call,
        execute_tool=execute_tool,
        update_conversation=update_conversation,
    ):
        results.append(r)

    # First yield: tool call iteration (not finished)
    # Second yield: text response (finished)
    assert len(results) == 2
    assert results[0].finished_naturally is False
    assert results[0].iterations == 1
    assert len(results[0].last_tool_calls) == 1
    assert results[1].finished_naturally is True
    assert results[1].response_text == "It's sunny in NYC"
    assert results[1].iterations == 2
    assert results[1].total_prompt_tokens == 20
    assert results[1].total_completion_tokens == 10