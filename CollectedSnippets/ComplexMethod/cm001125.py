async def test_text_response_no_tool_calls():
    """LLM responds with text only -- loop should yield once and finish."""

    async def llm_call(
        messages: list[dict[str, Any]], tools: Sequence[Any]
    ) -> LLMLoopResponse:
        return _make_response(text="Hello world")

    async def execute_tool(
        tool_call: LLMToolCall, tools: Sequence[Any]
    ) -> ToolCallResult:
        raise AssertionError("Should not be called")

    def update_conversation(
        messages: list[dict[str, Any]],
        response: LLMLoopResponse,
        tool_results: list[ToolCallResult] | None = None,
    ) -> None:
        messages.append({"role": "assistant", "content": response.response_text})

    msgs: list[dict[str, Any]] = [{"role": "user", "content": "Hi"}]
    results: list[ToolCallLoopResult] = []
    async for r in tool_call_loop(
        messages=msgs,
        tools=TOOL_DEFS,
        llm_call=llm_call,
        execute_tool=execute_tool,
        update_conversation=update_conversation,
    ):
        results.append(r)

    assert len(results) == 1
    assert results[0].finished_naturally is True
    assert results[0].response_text == "Hello world"
    assert results[0].iterations == 1
    assert results[0].total_prompt_tokens == 10
    assert results[0].total_completion_tokens == 5