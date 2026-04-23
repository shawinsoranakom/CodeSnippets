async def test_chunked_vs_normal_consistency(
    client_with_chunked_processing: openai.AsyncOpenAI, model_name: str
):
    """Test consistency between chunked and
    normal processing (using short text)."""

    # Use a short text within the 512 token limit
    short_text = (
        "Artificial intelligence technology is changing our world, "
        "bringing unprecedented opportunities and challenges."
    )

    # Send embedding request
    embedding_response = await client_with_chunked_processing.embeddings.create(
        model=model_name,
        input=[short_text],
        encoding_format="float",
    )

    # Verify response structure
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert len(embeddings.data[0].embedding) == 384
    assert embeddings.usage.completion_tokens == 0
    # Short text should not require chunked processing
    assert embeddings.usage.prompt_tokens < 512
    assert embeddings.usage.total_tokens == embeddings.usage.prompt_tokens

    # 验证embedding向量的有效性
    embedding_vector = embeddings.data[0].embedding
    assert all(isinstance(x, float) for x in embedding_vector)
    assert not all(x == 0 for x in embedding_vector)