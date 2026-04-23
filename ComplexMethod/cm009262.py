def test_bind_tools_drops_forced_tool_choice_when_adaptive_thinking() -> None:
    """Adaptive thinking has the same forced tool_choice restriction as enabled."""
    chat_model = ChatAnthropic(
        model=MODEL_NAME,
        anthropic_api_key="secret-api-key",
        thinking={"type": "adaptive"},
    )

    # tool_choice="any" should be dropped with warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = chat_model.bind_tools([GetWeather], tool_choice="any")
    assert "tool_choice" not in cast("RunnableBinding", result).kwargs
    assert len(w) == 1
    assert "thinking is enabled" in str(w[0].message)

    # tool_choice="auto" should NOT be dropped (auto is allowed)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = chat_model.bind_tools([GetWeather], tool_choice="auto")
    assert cast("RunnableBinding", result).kwargs["tool_choice"] == {"type": "auto"}
    assert len(w) == 0

    # tool_choice=specific tool name should be dropped with warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = chat_model.bind_tools([GetWeather], tool_choice="GetWeather")
    assert "tool_choice" not in cast("RunnableBinding", result).kwargs
    assert len(w) == 1

    # tool_choice=dict with type "tool" should be dropped with warning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = chat_model.bind_tools(
            [GetWeather],
            tool_choice={"type": "tool", "name": "GetWeather"},
        )
    assert "tool_choice" not in cast("RunnableBinding", result).kwargs
    assert len(w) == 1

    # tool_choice=dict with type "any" should also be dropped
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = chat_model.bind_tools(
            [GetWeather],
            tool_choice={"type": "any"},
        )
    assert "tool_choice" not in cast("RunnableBinding", result).kwargs
    assert len(w) == 1