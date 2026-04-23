def test_set_default_max_tokens() -> None:
    """Test the set_default_max_tokens function."""
    # Test claude-sonnet-4-5 models
    llm = ChatAnthropic(model="claude-sonnet-4-5-20250929", anthropic_api_key="test")
    assert llm.max_tokens == 64000

    # Test claude-opus-4 models
    llm = ChatAnthropic(model="claude-opus-4-20250514", anthropic_api_key="test")
    assert llm.max_tokens == 32000

    # Test claude-sonnet-4 models
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", anthropic_api_key="test")
    assert llm.max_tokens == 64000

    # Test claude-3-7-sonnet models
    llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", anthropic_api_key="test")
    assert llm.max_tokens == 64000

    # Test claude-3-5-haiku models
    llm = ChatAnthropic(model="claude-3-5-haiku-20241022", anthropic_api_key="test")
    assert llm.max_tokens == 8192

    # Test claude-3-haiku models (should default to 4096)
    llm = ChatAnthropic(model="claude-3-haiku-20240307", anthropic_api_key="test")
    assert llm.max_tokens == 4096

    # Test that existing max_tokens values are preserved
    llm = ChatAnthropic(model=MODEL_NAME, max_tokens=2048, anthropic_api_key="test")
    assert llm.max_tokens == 2048

    # Test that explicitly set max_tokens values are preserved
    llm = ChatAnthropic(model=MODEL_NAME, max_tokens=4096, anthropic_api_key="test")
    assert llm.max_tokens == 4096