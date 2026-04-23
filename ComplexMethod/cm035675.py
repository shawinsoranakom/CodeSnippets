def test_llm_summarizing_condenser_keeps_first_and_summary_events(
    mock_llm, mock_llm_registry
):
    """Test that the LLM summarizing condenser appropriately maintains the event prefix and any summary events."""
    max_size = 10
    keep_first = 3
    condenser = LLMSummarizingCondenser(
        max_size=max_size,
        keep_first=keep_first,
        llm=mock_llm,
    )

    mock_llm.set_mock_response_content('Summary of forgotten events')

    events = [create_test_event(f'Event {i}', id=i) for i in range(max_size * 10)]
    harness = RollingCondenserTestHarness(condenser)

    for i, view in enumerate(harness.views(events)):
        assert len(view) == harness.expected_size(i, max_size)

        # Ensure that the we've called out the summarizing LLM once per condensation
        assert mock_llm.completion.call_count == harness.expected_condensations(
            i, max_size
        )

        # Ensure that the prefix is appropiately maintained
        assert view[:keep_first] == events[: min(keep_first, i + 1)]

        # If we've condensed, ensure that the summary event is present
        if i > max_size:
            assert isinstance(view[keep_first], AgentCondensationObservation)