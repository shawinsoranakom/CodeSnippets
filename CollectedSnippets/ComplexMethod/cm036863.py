async def test_reasoning_and_function_items(client: OpenAI, model_name: str):
    response = await client.responses.create(
        model=model_name,
        input=[
            {"type": "message", "content": "Hello.", "role": "user"},
            {
                "type": "reasoning",
                "id": "lol",
                "content": [
                    {
                        "type": "reasoning_text",
                        "text": "We need to respond: greeting.",
                    }
                ],
                "summary": [],
            },
            {
                "arguments": '{"location": "Paris", "unit": "celsius"}',
                "call_id": "call_5f7b38f3b81e4b8380fd0ba74f3ca3ab",
                "name": "get_weather",
                "type": "function_call",
                "id": "fc_4fe5d6fc5b6c4d6fa5f24cc80aa27f78",
                "status": "completed",
            },
            {
                "call_id": "call_5f7b38f3b81e4b8380fd0ba74f3ca3ab",
                "id": "fc_4fe5d6fc5b6c4d6fa5f24cc80aa27f78",
                "output": "The weather in Paris is 20 Celsius",
                "status": "completed",
                "type": "function_call_output",
            },
        ],
        temperature=0.0,
    )
    assert response is not None
    assert response.status == "completed"

    output_types = [getattr(o, "type", None) for o in response.output]
    assert "reasoning" in output_types, (
        f"Expected reasoning in output, got: {output_types}"
    )
    assert "message" in output_types, f"Expected message in output, got: {output_types}"

    msg = next(o for o in response.output if o.type == "message")
    assert type(msg.content[0].text) is str