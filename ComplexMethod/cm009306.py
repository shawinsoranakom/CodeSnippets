def test__stream_no_reasoning(model: str) -> None:
    """Test low-level chunk streaming of a simple prompt with `reasoning=False`."""
    llm = OllamaLLM(model=model, num_ctx=2**12)

    result_chunk = None
    for chunk in llm._stream(SAMPLE):
        assert isinstance(chunk, GenerationChunk)
        if result_chunk is None:
            result_chunk = chunk
        else:
            result_chunk += chunk

    # The final result must be a GenerationChunk with visible content
    assert isinstance(result_chunk, GenerationChunk)
    assert result_chunk.text
    assert result_chunk.generation_info
    assert not result_chunk.generation_info.get("reasoning_content")