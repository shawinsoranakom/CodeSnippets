async def test_function_tool_use(
    client: openai.AsyncOpenAI, model_name: str, tool_choice: str
):
    prompt = [
        {
            "role": "user",
            "content": "Can you tell me what the current weather is in Berlin and the "
            "forecast for the next 5 days, in fahrenheit?",
        },
    ]
    response = await client.responses.create(
        model=model_name,
        input=prompt,
        tools=tools,
        tool_choice=tool_choice,
        temperature=0.0,
    )
    assert len(response.output) >= 1
    tool_call = None
    reasoning = None
    for out in response.output:
        if out.type == "function_call":
            tool_call = out
        if out.type == "reasoning":
            reasoning = out
    if response.incomplete_details is None:
        assert tool_call is not None
        assert tool_call.type == "function_call"
        assert json.loads(tool_call.arguments) is not None
        assert reasoning is not None
        assert reasoning.type == "reasoning"
    else:
        print(response.model_dump_json(indent=2))
        assert response.incomplete_details.reason == "max_output_tokens"