async def test_json_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    model = "gpt-4.1-nano-2025-04-14"

    called_args = {}

    async def _mock_create(*args: Any, **kwargs: Any) -> ChatCompletion:
        # Capture the arguments passed to the function
        called_args["kwargs"] = kwargs
        return ChatCompletion(
            id="id1",
            choices=[
                Choice(
                    finish_reason="stop",
                    index=0,
                    message=ChatCompletionMessage(
                        content=json.dumps({"thoughts": "happy", "response": "happy"}),
                        role="assistant",
                    ),
                )
            ],
            created=0,
            model=model,
            object="chat.completion",
            usage=CompletionUsage(prompt_tokens=10, completion_tokens=5, total_tokens=0),
        )

    monkeypatch.setattr(AsyncCompletions, "create", _mock_create)
    model_client = OpenAIChatCompletionClient(model=model, api_key="")

    # Test that the openai client was called with the correct response format.
    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")], json_output=True
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"] == {"type": "json_object"}

    # Make sure that the response format is set to json_object when json_output is True, regardless of the extra_create_args.
    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        json_output=True,
        extra_create_args={"response_format": "json_object"},
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"] == {"type": "json_object"}

    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        json_output=True,
        extra_create_args={"response_format": "text"},
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    # Check that the openai client was called with the correct response format.
    assert called_args["kwargs"]["response_format"] == {"type": "json_object"}

    # Make sure when json_output is set to False, the response format is always set to text.
    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        json_output=False,
        extra_create_args={"response_format": "text"},
    )
    assert called_args["kwargs"]["response_format"] == {"type": "text"}

    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        json_output=False,
        extra_create_args={"response_format": "json_object"},
    )
    assert called_args["kwargs"]["response_format"] == {"type": "text"}

    # Make sure when response_format is set it is used when json_output is not set.
    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        extra_create_args={"response_format": {"type": "json_object"}},
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"] == {"type": "json_object"}