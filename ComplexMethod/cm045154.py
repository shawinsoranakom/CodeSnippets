async def test_create_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    class ResponseType(BaseModel):
        response: str

    model = "llama3.2"

    async def _mock_chat(*args: Any, **kwargs: Any) -> ChatResponse:
        return ChatResponse(
            model=model,
            done=True,
            done_reason="stop",
            message=Message(
                role="assistant",
                content=json.dumps({"response": "Hello world!"}),
            ),
            prompt_eval_count=10,
            eval_count=12,
        )

    monkeypatch.setattr(AsyncClient, "chat", _mock_chat)

    client = OllamaChatCompletionClient(model=model)
    create_result = await client.create(
        messages=[
            UserMessage(content="hi", source="user"),
        ],
        json_output=ResponseType,
    )
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0
    assert create_result.finish_reason == "stop"
    assert create_result.usage is not None
    assert create_result.usage.prompt_tokens == 10
    assert create_result.usage.completion_tokens == 12
    assert ResponseType.model_validate_json(create_result.content)

    create_result = await client.create(
        messages=[
            UserMessage(content="hi", source="user"),
        ],
        extra_create_args={"format": ResponseType.model_json_schema()},
    )
    assert isinstance(create_result.content, str)
    assert len(create_result.content) > 0
    assert create_result.finish_reason == "stop"
    assert create_result.usage is not None
    assert create_result.usage.prompt_tokens == 10
    assert create_result.usage.completion_tokens == 12
    assert ResponseType.model_validate_json(create_result.content)

    # Test case when response_format is in extra_create_args.
    with pytest.warns(DeprecationWarning, match="Using response_format will be deprecated. Use json_output instead."):
        create_result = await client.create(
            messages=[
                UserMessage(content="hi", source="user"),
            ],
            extra_create_args={"response_format": ResponseType},
        )

    # Test case when response_format is in extra_create_args but is not a pydantic model.
    with pytest.raises(ValueError, match="response_format must be a Pydantic model class"):
        create_result = await client.create(
            messages=[
                UserMessage(content="hi", source="user"),
            ],
            extra_create_args={"response_format": "json"},
        )

    # Test case when response_format is in extra_create_args and json_output is also set.
    with pytest.raises(
        ValueError,
        match="response_format and json_output cannot be set to a Pydantic model class at the same time. Use json_output instead.",
    ):
        create_result = await client.create(
            messages=[
                UserMessage(content="hi", source="user"),
            ],
            extra_create_args={"response_format": ResponseType},
            json_output=ResponseType,
        )

    # Test case when format is in extra_create_args and json_output is also set.
    with pytest.raises(
        ValueError, match="json_output and format cannot be set at the same time. Use json_output instead."
    ):
        create_result = await client.create(
            messages=[
                UserMessage(content="hi", source="user"),
            ],
            extra_create_args={"format": ResponseType.model_json_schema()},
            json_output=ResponseType,
        )