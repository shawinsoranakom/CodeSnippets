async def test_stream_with_logprobs():
    """Streaming with logprobs includes logprob data in each chunk."""
    engine = _mock_engine()

    async def mock_generate(*args, **kwargs):
        yield _make_request_output(
            "req-1",
            token_ids=[10],
            logprobs=[{10: Logprob(logprob=-0.5)}],
        )
        yield _make_request_output(
            "req-1",
            token_ids=[20],
            logprobs=[{20: Logprob(logprob=-1.0)}],
            finish_reason="stop",
            finished=True,
        )

    engine.generate = MagicMock(side_effect=mock_generate)
    serving = _build_serving_tokens(engine)

    request = GenerateRequest(
        token_ids=[1, 2, 3],
        sampling_params=SamplingParams(max_tokens=10, logprobs=1),
        model=MODEL_NAME,
        stream=True,
    )

    response = await serving.serve_tokens(request)
    chunks = []
    async for chunk in response:
        chunks.append(chunk)

    parsed = _parse_sse_chunks(chunks)
    data_chunks = [c for c in parsed if isinstance(c, dict) and c.get("choices")]

    for dc in data_chunks:
        lp = dc["choices"][0]["logprobs"]
        assert lp is not None
        assert len(lp["content"]) == 1
        assert lp["content"][0]["token"].startswith("token_id:")