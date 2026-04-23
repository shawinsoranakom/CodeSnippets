def test_perplexity_stream_includes_citations(mocker: MockerFixture) -> None:
    """Test that the stream method includes citations in the additional_kwargs."""
    llm = ChatPerplexity(model="test", timeout=30, verbose=True)
    mock_chunk_0 = {
        "choices": [{"delta": {"content": "Hello "}, "finish_reason": None}],
        "citations": ["example.com", "example2.com"],
    }
    mock_chunk_1 = {
        "choices": [{"delta": {"content": "Perplexity"}, "finish_reason": None}],
        "citations": ["example.com", "example2.com"],
    }
    mock_chunk_2 = {
        "choices": [{"delta": {}, "finish_reason": "stop"}],
    }
    mock_chunks: list[dict[str, Any]] = [mock_chunk_0, mock_chunk_1, mock_chunk_2]
    mock_stream = MagicMock()
    mock_stream.__iter__.return_value = mock_chunks
    patcher = mocker.patch.object(
        llm.client.chat.completions, "create", return_value=mock_stream
    )
    stream = llm.stream("Hello langchain")
    full: BaseMessage | None = None
    chunks_list = list(stream)
    # BaseChatModel.stream() adds an extra chunk after the final chunk from _stream
    assert len(chunks_list) == 4
    for i, chunk in enumerate(
        chunks_list[:3]
    ):  # Only check first 3 chunks against mock
        full = chunk if full is None else cast(BaseMessage, full + chunk)
        assert chunk.content == mock_chunks[i]["choices"][0]["delta"].get("content", "")
        if i == 0:
            assert chunk.additional_kwargs["citations"] == [
                "example.com",
                "example2.com",
            ]
        else:
            assert "citations" not in chunk.additional_kwargs
    # Process the 4th chunk
    assert full is not None
    full = cast(BaseMessage, full + chunks_list[3])
    assert isinstance(full, AIMessageChunk)
    assert full.content == "Hello Perplexity"
    assert full.additional_kwargs == {"citations": ["example.com", "example2.com"]}

    patcher.assert_called_once()