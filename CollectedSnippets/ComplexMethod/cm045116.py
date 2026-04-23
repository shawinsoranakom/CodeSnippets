async def test_structured_output_using_response_format(monkeypatch: pytest.MonkeyPatch) -> None:
    class AgentResponse(BaseModel):
        thoughts: str
        response: Literal["happy", "sad", "neutral"]

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

    # Scenario 1: response_format is set to constructor.
    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key="",
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "test",
                "description": "test",
                "schema": AgentResponse.model_json_schema(),
            },
        },
    )

    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"]["type"] == "json_schema"

    # Test the response format can be serailized and deserialized.
    config = model_client.dump_component()
    assert config
    loaded_client = OpenAIChatCompletionClient.load_component(config)

    create_result = await loaded_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"]["type"] == "json_schema"

    # Scenario 2: response_format is set to a extra_create_args.
    model_client = OpenAIChatCompletionClient(model=model, api_key="")
    create_result = await model_client.create(
        messages=[UserMessage(content="I am happy.", source="user")],
        extra_create_args={
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "description": "test",
                    "schema": AgentResponse.model_json_schema(),
                },
            }
        },
    )
    assert isinstance(create_result.content, str)
    response = json.loads(create_result.content)
    assert response["thoughts"] == "happy"
    assert response["response"] == "happy"
    assert called_args["kwargs"]["response_format"]["type"] == "json_schema"