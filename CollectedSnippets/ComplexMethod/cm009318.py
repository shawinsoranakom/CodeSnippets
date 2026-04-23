def test_reasoning_modes_behavior(model: str) -> None:
    """Test the behavior differences between reasoning modes.

    This test documents how the Ollama API and LangChain handle reasoning content
    for DeepSeek R1 models across different reasoning settings.

    Current Ollama API behavior:
    - Ollama automatically separates reasoning content into a 'thinking' field
    - No <think> tags are present in responses
    - `think=False` prevents the 'thinking' field from being included
    - `think=None` includes the 'thinking' field (model default)
    - `think=True` explicitly requests the 'thinking' field

    LangChain behavior:
    - `reasoning=False`: Does not capture reasoning content
    - `reasoning=None`: Does not capture reasoning content (model default behavior)
    - `reasoning=True`: Captures reasoning in `additional_kwargs['reasoning_content']`
    """
    message = HumanMessage(content=SAMPLE)

    # Test with reasoning=None (model default - no reasoning captured)
    llm_default = ChatOllama(model=model, reasoning=None, num_ctx=2**12)
    result_default = llm_default.invoke([message])
    assert result_default.content
    assert "<think>" not in result_default.content
    assert "</think>" not in result_default.content
    assert "reasoning_content" not in result_default.additional_kwargs

    # Test with reasoning=False (explicit disable - no reasoning captured)
    llm_disabled = ChatOllama(model=model, reasoning=False, num_ctx=2**12)
    result_disabled = llm_disabled.invoke([message])
    assert result_disabled.content
    assert "<think>" not in result_disabled.content
    assert "</think>" not in result_disabled.content
    assert "reasoning_content" not in result_disabled.additional_kwargs

    # Test with reasoning=True (reasoning captured separately)
    llm_enabled = ChatOllama(model=model, reasoning=True, num_ctx=2**12)
    result_enabled = llm_enabled.invoke([message])
    assert result_enabled.content
    assert "<think>" not in result_enabled.content
    assert "</think>" not in result_enabled.content
    assert "reasoning_content" in result_enabled.additional_kwargs
    assert len(result_enabled.additional_kwargs["reasoning_content"]) > 0
    assert "<think>" not in result_enabled.additional_kwargs["reasoning_content"]
    assert "</think>" not in result_enabled.additional_kwargs["reasoning_content"]