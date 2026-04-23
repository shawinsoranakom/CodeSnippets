def test_condenser_pipeline_chains_sub_condensers():
    """Test that the CondenserPipeline chains sub-condensers and combines their behavior."""
    MAX_SIZE = 10
    ATTENTION_WINDOW = 2
    NUMBER_OF_CONDENSATIONS = 3

    condenser = CondenserPipeline(
        AmortizedForgettingCondenser(max_size=MAX_SIZE),
        BrowserOutputCondenser(attention_window=ATTENTION_WINDOW),
    )

    harness = RollingCondenserTestHarness(condenser)
    events = [
        BrowserOutputObservation(
            f'Observation {i}', url='', trigger_by_action=ActionType.BROWSE
        )
        if i % 3 == 0
        else create_test_event(f'Event {i}')
        for i in range(0, MAX_SIZE * NUMBER_OF_CONDENSATIONS)
    ]

    for index, view in enumerate(harness.views(events)):
        # The amortized forgetting condenser is responsible for keeping the size
        # bounded despite the large number of events.
        assert len(view) == harness.expected_size(index, MAX_SIZE)

        # The browser output condenser should mask out the content of all the
        # browser observations outside the attention window (which is relative
        # to the number of browser outputs in the view, not the whole view or
        # the event stream).
        browser_outputs = [
            event
            for event in view
            if isinstance(
                event, (BrowserOutputObservation, AgentCondensationObservation)
            )
        ]

        for event in browser_outputs[:-ATTENTION_WINDOW]:
            assert 'Content omitted' in str(event)

        for event in browser_outputs[-ATTENTION_WINDOW:]:
            assert 'Content omitted' not in str(event)