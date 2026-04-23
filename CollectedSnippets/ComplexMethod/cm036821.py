async def test_tool_response_schema_accuracy(client: openai.AsyncOpenAI):
    """Validate that tool call arguments adhere to their declared JSON schema."""
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=MESSAGES_MULTIPLE_CALLS,
        tools=TOOLS,
        temperature=0.0,
    )

    calls = response.choices[0].message.tool_calls
    assert calls, "No tool calls produced"

    for call in calls:
        func_name = call.function.name
        args = json.loads(call.function.arguments)

        schema: dict[str, object] | None = None
        for tool_entry in TOOLS:
            function_def = tool_entry.get("function")
            if (
                function_def
                and isinstance(function_def, dict)
                and function_def.get("name") == func_name
            ):
                schema = function_def.get("parameters")
                break

        assert schema is not None, f"No matching tool schema found for {func_name}"

        jsonschema.validate(instance=args, schema=schema)