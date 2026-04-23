async def test_map_query_uses_query_config():
    """map_query_semantic_space should call perform_completion_with_backoff
    with the query LLM config (chat model), NOT the embedding config."""

    config = AdaptiveConfig(
        strategy="embedding",
        embedding_llm_config=LLMConfig(
            provider="openai/text-embedding-3-small",
            api_token="emb-key",
            base_url="https://emb.example.com",
        ),
        query_llm_config=LLMConfig(
            provider="openai/gpt-4o-mini",
            api_token="query-key",
            base_url="https://query.example.com",
        ),
    )

    strategy = EmbeddingStrategy(
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_config=config.embedding_llm_config,
        query_llm_config=config.query_llm_config,
    )
    strategy.config = config

    # Mock perform_completion_with_backoff to capture its arguments
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "queries": [f"variation {i}" for i in range(13)]
    })

    captured_kwargs = {}

    def mock_completion(**kwargs):
        # Also accept positional-style
        captured_kwargs.update(kwargs)
        return mock_response

    # Also mock _get_embeddings to avoid real embedding calls
    fake_embeddings = np.random.rand(11, 384).astype(np.float32)

    with patch("crawl4ai.utils.perform_completion_with_backoff", side_effect=mock_completion):
        with patch.object(strategy, "_get_embeddings", new_callable=AsyncMock, return_value=fake_embeddings):
            await strategy.map_query_semantic_space("test query", n_synthetic=10)

    # Verify the query config was used, NOT the embedding config
    assert captured_kwargs["provider"] == "openai/gpt-4o-mini", \
        f"Expected query model, got {captured_kwargs['provider']}"
    assert captured_kwargs["api_token"] == "query-key", \
        f"Expected query-key, got {captured_kwargs['api_token']}"
    assert captured_kwargs["base_url"] == "https://query.example.com", \
        f"Expected query base_url, got {captured_kwargs['base_url']}"

    # Verify backoff params are passed (bug fix)
    assert "base_delay" in captured_kwargs
    assert "max_attempts" in captured_kwargs
    assert "exponential_factor" in captured_kwargs

    print("PASS: test_map_query_uses_query_config")