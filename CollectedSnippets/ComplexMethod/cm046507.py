def test_openai_tools_nonstream(base_url: str, api_key: str):
    """Standard OpenAI function calling, non-streaming, tool_choice='required'.

    Regression: before the fix, Studio silently stripped `tools` and the
    model returned plain text with finish_reason='stop'. After the fix,
    llama-server's response is forwarded verbatim so the client sees
    finish_reason='tool_calls' with a structured tool_calls array and
    non-zero usage.prompt_tokens.
    """
    status, text = _http(
        "POST",
        f"{base_url}/v1/chat/completions",
        body = {
            "messages": [{"role": "user", "content": "What is the weather in Paris?"}],
            "tools": [_WEATHER_TOOL],
            "tool_choice": "required",
            "stream": False,
        },
        headers = {"Authorization": f"Bearer {api_key}"},
        timeout = 120,
    )
    assert status == 200, f"Expected 200, got {status}: {text[:500]}"
    data = json.loads(text)
    assert "choices" in data, f"Missing 'choices': {text[:300]}"
    choice = data["choices"][0]
    assert (
        choice["finish_reason"] == "tool_calls"
    ), f"Expected finish_reason='tool_calls', got {choice['finish_reason']!r}"
    msg = choice["message"]
    tool_calls = msg.get("tool_calls") or []
    assert len(tool_calls) >= 1, f"No tool_calls in response: {msg}"
    first = tool_calls[0]
    assert first["type"] == "function"
    assert (
        first["function"]["name"] == "get_weather"
    ), f"Wrong tool name: {first['function']['name']!r}"
    # arguments must be valid JSON
    parsed = json.loads(first["function"]["arguments"])
    assert "city" in parsed, f"Tool call missing required 'city' arg: {parsed}"
    # Usage must be non-zero (was 0 before the fix)
    usage = data.get("usage") or {}
    assert (
        usage.get("prompt_tokens", 0) > 0
    ), f"Expected non-zero prompt_tokens; got {usage}"
    assert data.get("id"), "Missing response id"
    print(
        f"  PASS  openai tools non-stream: "
        f"tool={first['function']['name']}, args={parsed}, "
        f"prompt_tokens={usage['prompt_tokens']}"
    )