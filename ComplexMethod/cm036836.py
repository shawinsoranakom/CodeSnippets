async def test_named_tool_use(
    client: openai.AsyncOpenAI,
    sample_json_schema,
):
    messages = [
        {"role": "system", "content": "you are a helpful assistant"},
        {
            "role": "user",
            "content": (
                "Give an example JSON for an employee profile using the specified tool."
            ),
        },
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "dummy_function_name",
                "description": "This is a dummy function",
                "parameters": sample_json_schema,
            },
        }
    ]
    tool_choice = {"type": "function", "function": {"name": "dummy_function_name"}}

    # non-streaming

    chat_completion = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_completion_tokens=1000,
        tools=tools,
        temperature=0.0,
        tool_choice=tool_choice,
    )
    message = chat_completion.choices[0].message
    assert len(message.content) == 0
    json_string = message.tool_calls[0].function.arguments
    json1 = json.loads(json_string)
    jsonschema.validate(instance=json1, schema=sample_json_schema)

    messages.append({"role": "assistant", "content": json_string})
    messages.append(
        {"role": "user", "content": "Give me another one with a different name and age"}
    )

    # streaming

    stream = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_completion_tokens=1000,
        tools=tools,
        tool_choice=tool_choice,
        temperature=0.0,
        stream=True,
    )

    output = []
    finish_reason_count = 0
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.role:
            assert delta.role == "assistant"
        assert delta.content is None or len(delta.content) == 0
        if delta.tool_calls:
            output.append(delta.tool_calls[0].function.arguments)
        if chunk.choices[0].finish_reason is not None:
            finish_reason_count += 1
    # finish reason should only return in last block
    assert finish_reason_count == 1
    json2 = json.loads("".join(output))
    jsonschema.validate(instance=json2, schema=sample_json_schema)
    assert json1["name"] != json2["name"]
    assert json1["age"] != json2["age"]