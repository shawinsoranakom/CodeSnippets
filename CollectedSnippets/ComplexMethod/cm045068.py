def test_embedding_function_config_validation() -> None:
    """Test validation of embedding function configurations."""

    # Test default config
    default_config = DefaultEmbeddingFunctionConfig()
    assert default_config.function_type == "default"

    # Test SentenceTransformer config
    st_config = SentenceTransformerEmbeddingFunctionConfig(model_name="test-model")
    assert st_config.function_type == "sentence_transformer"
    assert st_config.model_name == "test-model"

    # Test OpenAI config
    openai_config = OpenAIEmbeddingFunctionConfig(api_key="test-key", model_name="test-model")
    assert openai_config.function_type == "openai"
    assert openai_config.api_key == "test-key"
    assert openai_config.model_name == "test-model"

    # Test custom config
    def dummy_function() -> None:
        return None

    custom_config = CustomEmbeddingFunctionConfig(function=dummy_function, params={"test": "value"})
    assert custom_config.function_type == "custom"
    assert custom_config.function == dummy_function
    assert custom_config.params == {"test": "value"}