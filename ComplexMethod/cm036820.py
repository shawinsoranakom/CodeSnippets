async def test_calculator_tool_call_and_argument_accuracy(client: openai.AsyncOpenAI):
    """Verify calculator tool call is made and arguments are accurate."""

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=MESSAGES_CALC,
        tools=TOOLS,
        temperature=0.0,
        stream=False,
    )

    message = response.choices[0].message
    tool_calls = getattr(message, "tool_calls", [])
    assert tool_calls, "No tool calls detected"

    calc_call = next((c for c in tool_calls if c.function.name == FUNC_CALC), None)
    assert calc_call, "Calculator function not called"

    raw_args = calc_call.function.arguments
    assert raw_args, "Calculator arguments missing"
    assert "123" in raw_args and "456" in raw_args, (
        f"Expected values not in raw arguments: {raw_args}"
    )

    try:
        parsed_args = json.loads(raw_args)
    except json.JSONDecodeError:
        pytest.fail(f"Invalid JSON in calculator arguments: {raw_args}")

    expected_expr = "123 + 456"
    actual_expr = parsed_args.get("expression", "")
    similarity = fuzz.ratio(actual_expr, expected_expr)

    assert similarity > 90, (
        f"Expression mismatch: expected '{expected_expr}' "
        f"got '{actual_expr}' (similarity={similarity}%)"
    )