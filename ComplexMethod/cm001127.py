async def test_max_iterations_reached():
    """Loop should stop after max_iterations even if LLM keeps calling tools."""

    async def llm_call(
        messages: list[dict[str, Any]], tools: Sequence[Any]
    ) -> LLMLoopResponse:
        return _make_response(
            tool_calls=[
                LLMToolCall(id="tc_x", name="get_weather", arguments='{"city":"X"}')
            ]
        )

    async def execute_tool(
        tool_call: LLMToolCall, tools: Sequence[Any]
    ) -> ToolCallResult:
        return ToolCallResult(
            tool_call_id=tool_call.id, tool_name=tool_call.name, content="result"
        )

    def update_conversation(
        messages: list[dict[str, Any]],
        response: LLMLoopResponse,
        tool_results: list[ToolCallResult] | None = None,
    ) -> None:
        pass

    msgs: list[dict[str, Any]] = [{"role": "user", "content": "Go"}]
    results: list[ToolCallLoopResult] = []
    async for r in tool_call_loop(
        messages=msgs,
        tools=TOOL_DEFS,
        llm_call=llm_call,
        execute_tool=execute_tool,
        update_conversation=update_conversation,
        max_iterations=3,
    ):
        results.append(r)

    # 3 tool-call iterations + 1 final "max reached"
    assert len(results) == 4
    for r in results[:3]:
        assert r.finished_naturally is False
    final = results[-1]
    assert final.finished_naturally is False
    assert "3 iterations" in final.response_text
    assert final.iterations == 3