async def test_streaming_logprobs(client: OpenAI, model_name: str):
    """Test that streaming with logprobs returns valid logprob data on
    output_text.delta events and that top_logprobs has the requested count."""
    response = await client.responses.create(
        model=model_name,
        input="Say hello.",
        stream=True,
        top_logprobs=3,
        include=["message.output_text.logprobs"],
    )

    events = []
    async for event in response:
        events.append(event)

    assert len(events) > 0

    # Collect all output_text.delta events that carry logprobs
    text_delta_events = [e for e in events if e.type == "response.output_text.delta"]
    assert len(text_delta_events) > 0, "Expected at least one text delta event"

    for delta_event in text_delta_events:
        logprobs = delta_event.logprobs
        assert logprobs is not None, "logprobs should be present on text delta events"
        assert len(logprobs) > 0, "logprobs list should not be empty"
        for lp in logprobs:
            # Each logprob entry must have a token and a logprob value
            assert lp.token is not None
            assert isinstance(lp.logprob, float)
            assert lp.logprob <= 0.0, f"logprob should be <= 0, got {lp.logprob}"
            # top_logprobs should have up to 3 entries
            assert lp.top_logprobs is not None
            assert len(lp.top_logprobs) <= 3
            for tl in lp.top_logprobs:
                assert tl.token is not None
                assert isinstance(tl.logprob, float)

    # Verify that top_logprobs are actually populated, not always empty
    all_top_logprobs = [
        tl for e in text_delta_events for lp in e.logprobs for tl in lp.top_logprobs
    ]
    assert len(all_top_logprobs) > 0, (
        "Expected at least one top_logprobs entry across all delta events"
    )

    # Verify the completed event still has valid output
    completed = events[-1]
    assert completed.type == "response.completed"
    assert completed.response.status == "completed"