def test_anthropic_tool_choice_any(base_url: str, api_key: str):
    """Anthropic Messages API: ``tool_choice: {"type": "any"}`` must be
    honored (forwarded as OpenAI ``tool_choice: "required"`` to
    llama-server). Regression for the secondary fix bundled with #4999 —
    previously this field was accepted on the request model but silently
    dropped with a warning log, so the model was free to answer from
    memory instead of using the tool.
    """
    status, events = _stream_anthropic_http(
        f"{base_url}/v1/messages",
        body = {
            "model": "default",
            "max_tokens": 256,
            "messages": [
                # A question the model could easily answer from memory if
                # tool_choice were not enforced.
                {
                    "role": "user",
                    "content": "What is the weather in London right now?",
                }
            ],
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Look up current weather for a city.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "city": {"type": "string"},
                        },
                        "required": ["city"],
                    },
                }
            ],
            "tool_choice": {"type": "any"},
            "stream": True,
        },
        headers = {"Authorization": f"Bearer {api_key}"},
        timeout = 120,
    )
    assert status == 200, f"Expected 200, got {status}"
    assert len(events) > 0, "No SSE events received"

    # With tool_choice=any, stop_reason must be tool_use (not end_turn)
    stop_reason = None
    for etype, data in events:
        if etype == "message_delta":
            stop_reason = data.get("delta", {}).get("stop_reason") or stop_reason
    assert stop_reason == "tool_use", (
        f"Expected stop_reason='tool_use' with tool_choice=any, got "
        f"{stop_reason!r} — tool_choice may not be forwarded to llama-server."
    )

    # And at least one tool_use content block must be emitted
    tool_use_starts = [
        e
        for e in events
        if e[0] == "content_block_start"
        and e[1].get("content_block", {}).get("type") == "tool_use"
    ]
    assert len(tool_use_starts) >= 1, "No tool_use content block emitted"
    print(
        f"  PASS  anthropic tool_choice=any honored: "
        f"{len(tool_use_starts)} tool_use blocks, stop_reason={stop_reason}"
    )