async def test_stream_skips_empty_token_output():
    """Outputs with empty token_ids are skipped (no chunk emitted)."""
    engine = _mock_engine()

    async def mock_generate(*args, **kwargs):
        yield _make_request_output("req-1", token_ids=[10])
        yield _make_request_output("req-1", token_ids=[])
        yield _make_request_output(
            "req-1", token_ids=[20], finish_reason="stop", finished=True
        )

    engine.generate = MagicMock(side_effect=mock_generate)
    serving = _build_serving_tokens(engine)

    request = GenerateRequest(
        token_ids=[1, 2, 3],
        sampling_params=SamplingParams(max_tokens=10),
        model=MODEL_NAME,
        stream=True,
    )

    response = await serving.serve_tokens(request)
    chunks = []
    async for chunk in response:
        chunks.append(chunk)

    parsed = _parse_sse_chunks(chunks)
    assert parsed[-1] == "[DONE]"
    data_chunks = [c for c in parsed if c != "[DONE]"]

    # Only 2 data chunks — the empty one is skipped
    assert len(data_chunks) == 2
    assert data_chunks[0]["choices"][0]["token_ids"] == [10]
    assert data_chunks[1]["choices"][0]["token_ids"] == [20]