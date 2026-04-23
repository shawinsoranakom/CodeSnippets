async def test__astream_with_reasoning(model: str) -> None:
    """Test low-level async chunk streaming with `reasoning=True`."""
    llm = OllamaLLM(model=model, num_ctx=2**12, reasoning=True)

    result_chunk = None
    async for chunk in llm._astream(SAMPLE):
        assert isinstance(chunk, GenerationChunk)
        if result_chunk is None:
            result_chunk = chunk
        else:
            result_chunk += chunk

    assert isinstance(result_chunk, GenerationChunk)
    assert result_chunk.text

    # Should have extracted reasoning into generation_info
    assert result_chunk.generation_info
    reasoning_content = result_chunk.generation_info.get("reasoning_content")
    assert reasoning_content
    assert len(reasoning_content) > 0
    # And neither the visible nor the hidden portion contains <think> tags
    assert "<think>" not in result_chunk.text
    assert "</think>" not in result_chunk.text
    assert "<think>" not in reasoning_content
    assert "</think>" not in reasoning_content