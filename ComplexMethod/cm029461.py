async def test_openai_provider_session_omits_prompt_cache_key_across_turns() -> None:
    client = _FakeOpenAIClient()
    session = OpenAIProviderSession(
        client=client,  # type: ignore[arg-type]
        model=Llm.GPT_5_2_CODEX_HIGH,
        prompt_messages=[{"role": "user", "content": "Build a landing page."}],
        tools=_test_tools(),
    )

    first_turn = await session.stream_turn(_noop_event_sink)
    session.append_tool_results(
        ProviderTurn(
            assistant_text=first_turn.assistant_text,
            tool_calls=[],
            assistant_turn=[
                {
                    "type": "function_call",
                    "call_id": "call-1",
                    "name": "edit_file",
                    "arguments": '{"path":"index.html"}',
                }
            ],
        ),
        [
            ExecutedToolCall(
                tool_call=ToolCall(
                    id="call-1",
                    name="edit_file",
                    arguments={"path": "index.html"},
                ),
                result=ToolExecutionResult(
                    ok=True,
                    result={
                        "content": "Successfully edited file at index.html.",
                        "details": {
                            "diff": "--- index.html\n+++ index.html\n@@ -1 +1 @@\n-a\n+b\n",
                            "firstChangedLine": 1,
                        },
                    },
                    summary={"content": "Successfully edited file at index.html."},
                ),
            )
        ],
    )
    await session.stream_turn(_noop_event_sink)

    first_call = client.responses.calls[0]
    second_call = client.responses.calls[1]
    first_input = first_call["input"]
    second_input = second_call["input"]

    assert "prompt_cache_key" not in first_call
    assert "prompt_cache_key" not in second_call
    assert "prompt_cache_retention" not in first_call
    assert "prompt_cache_retention" not in second_call
    assert isinstance(first_input, list)
    assert isinstance(second_input, list)
    assert len(second_input) > len(first_input)