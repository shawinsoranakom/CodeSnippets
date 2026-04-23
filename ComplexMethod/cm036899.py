async def test_batch_long_text_embedding(
    client_with_chunked_processing: openai.AsyncOpenAI, model_name: str
):
    """Test batch long text embedding processing."""

    input_texts = [
        LONG_TEXT_1500_WORDS,
        LONG_TEXT_2500_WORDS,
        "This is a short text test.",  # Short text for comparison
    ]

    # Send batch embedding request
    embedding_response = await client_with_chunked_processing.embeddings.create(
        model=model_name,
        input=input_texts,
        encoding_format="float",
    )

    # Verify response structure
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 3  # Three input texts

    # Verify each embedding dimension
    for i, embedding_data in enumerate(embeddings.data):
        assert len(embedding_data.embedding) == 384
        assert embedding_data.index == i

        # Verify embedding vector validity
        embedding_vector = embedding_data.embedding
        assert all(isinstance(x, float) for x in embedding_vector)
        assert not all(x == 0 for x in embedding_vector)

    # Verify token usage
    assert embeddings.usage.completion_tokens == 0
    # Total token count should be very substantial
    assert embeddings.usage.prompt_tokens > 1000
    assert embeddings.usage.total_tokens == embeddings.usage.prompt_tokens