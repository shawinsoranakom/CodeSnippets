async def test_long_text_embedding_1500_chars(
    client_with_chunked_processing: openai.AsyncOpenAI, model_name: str
):
    """Test embedding processing for ~1500 character long text
    (~1028 tokens, exceeding 512 token limit)."""

    # Verify text length
    # Verify text has sufficient word count (approximately 1500 words)
    word_count = len(LONG_TEXT_1500_WORDS.split())
    assert word_count >= 1400, f"Test text word count insufficient: {word_count} words"

    # Send embedding request
    embedding_response = await client_with_chunked_processing.embeddings.create(
        model=model_name,
        input=[LONG_TEXT_1500_WORDS],
        encoding_format="float",
    )

    # Verify response structure
    embeddings = EmbeddingResponse.model_validate(
        embedding_response.model_dump(mode="json")
    )

    assert embeddings.id is not None
    assert len(embeddings.data) == 1
    assert (
        len(embeddings.data[0].embedding) == 384
    )  # multilingual-e5-small embedding dimension
    assert embeddings.usage.completion_tokens == 0
    # Due to chunked processing, token count should
    # reflect actual processed tokens
    # With ~1500 words, we expect roughly
    # 1024+ tokens (exceeding 512 token limit)
    # Should exceed single chunk limit of 512
    assert embeddings.usage.prompt_tokens > 800
    assert embeddings.usage.total_tokens == embeddings.usage.prompt_tokens

    # Verify embedding vector validity
    embedding_vector = embeddings.data[0].embedding
    assert all(isinstance(x, float) for x in embedding_vector), (
        "Embedding vector should contain floats"
    )
    assert not all(x == 0 for x in embedding_vector), (
        "Embedding vector should not be all zeros"
    )