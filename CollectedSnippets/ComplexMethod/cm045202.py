def test_azure_openai_endpoint_validation() -> None:
    """Test validation of Azure OpenAI endpoint for client-side embeddings."""
    config = AzureAISearchConfig(
        name="test_tool",
        endpoint="https://test.search.windows.net",
        index_name="test-index",
        credential=AzureKeyCredential("test-key"),
        embedding_provider="azure_openai",
        embedding_model="text-embedding-ada-002",
        openai_endpoint="https://test.openai.azure.com",
    )
    assert config.embedding_provider == "azure_openai"
    assert config.embedding_model == "text-embedding-ada-002"
    assert config.openai_endpoint == "https://test.openai.azure.com"

    with pytest.raises(ValidationError) as exc:
        AzureAISearchConfig(
            name="test_tool",
            endpoint="https://test.search.windows.net",
            index_name="test-index",
            credential=AzureKeyCredential("test-key"),
            embedding_provider="azure_openai",
            embedding_model="text-embedding-ada-002",
        )
    assert "openai_endpoint must be provided for azure_openai" in str(exc.value)

    config = AzureAISearchConfig(
        name="test_tool",
        endpoint="https://test.search.windows.net",
        index_name="test-index",
        credential=AzureKeyCredential("test-key"),
        embedding_provider="openai",
        embedding_model="text-embedding-ada-002",
    )
    assert config.embedding_provider == "openai"
    assert config.embedding_model == "text-embedding-ada-002"
    assert config.openai_endpoint is None