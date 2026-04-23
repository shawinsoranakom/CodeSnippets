async def test_stream_continuous_usage():
    """continuous_usage_stats adds usage to every data chunk."""
    engine = _mock_engine()

    async def mock_generate(*args, **kwargs):
        yield _make_request_output("req-1", token_ids=[10])
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
        stream_options=StreamOptions(
            include_usage=True,
            continuous_usage_stats=True,
        ),
    )

    response = await serving.serve_tokens(request)
    chunks = []
    async for chunk in response:
        chunks.append(chunk)

    parsed = _parse_sse_chunks(chunks)
    data_chunks = [c for c in parsed if isinstance(c, dict) and c.get("choices")]

    # Every data chunk should have usage
    for i, dc in enumerate(data_chunks):
        assert dc["usage"] is not None, f"chunk {i} missing usage"
        assert dc["usage"]["prompt_tokens"] == 3

    # First chunk: 1 completion token
    assert data_chunks[0]["usage"]["completion_tokens"] == 1
    assert data_chunks[0]["usage"]["total_tokens"] == 4

    # Second chunk: 2 completion tokens (cumulative)
    assert data_chunks[1]["usage"]["completion_tokens"] == 2
    assert data_chunks[1]["usage"]["total_tokens"] == 5