def test_strict_mode(*, use_responses_api: bool) -> None:
    model_kwargs: dict[str, Any] = {"model": "gpt-5", "use_responses_api": use_responses_api}

    if "OPENAI_API_KEY" not in os.environ:
        model_kwargs["api_key"] = "foo"

    model = ChatOpenAI(**model_kwargs)

    # spy on _get_request_payload to check that `strict` is enabled
    original_method = model._get_request_payload
    payloads = []

    def capture_payload(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original_method(*args, **kwargs)
        payloads.append(result)
        return result

    with patch.object(model, "_get_request_payload", side_effect=capture_payload):
        agent = create_agent(
            model,
            tools=[get_weather],
            response_format=ProviderStrategy(WeatherBaseModel, strict=True),
        )
        response = agent.invoke({"messages": [HumanMessage("What's the weather in Boston?")]})

        assert len(payloads) == 2
        if use_responses_api:
            assert payloads[-1]["text"]["format"]["strict"]
        else:
            assert payloads[-1]["response_format"]["json_schema"]["strict"]

    assert isinstance(response["structured_response"], WeatherBaseModel)
    assert response["structured_response"].temperature == 75.0
    assert response["structured_response"].condition.lower() == "sunny"
    assert len(response["messages"]) == 4

    assert [m.type for m in response["messages"]] == [
        "human",  # "What's the weather?"
        "ai",  # "What's the weather?"
        "tool",  # "The weather is sunny and 75°F."
        "ai",  # structured response
    ]