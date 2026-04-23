async def test_enable_response_messages(client: OpenAI, model_name: str):
    response = await client.responses.create(
        model=model_name,
        input="Hello?",
        extra_body={"enable_response_messages": True},
    )
    assert response.status == "completed"
    assert response.input_messages[0]["type"] == "raw_message_tokens"
    assert type(response.input_messages[0]["message"]) is str
    assert len(response.input_messages[0]["message"]) > 10
    assert type(response.input_messages[0]["tokens"][0]) is int
    assert type(response.output_messages[0]["message"]) is str
    assert len(response.output_messages[0]["message"]) > 10
    assert type(response.output_messages[0]["tokens"][0]) is int