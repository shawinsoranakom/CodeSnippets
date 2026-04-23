def test_browser_output_condenser_respects_attention_window():
    """Test that BrowserOutputCondenser only masks events outside the attention window."""
    attention_window = 3
    condenser = BrowserOutputCondenser(attention_window=attention_window)

    events = [
        BrowserOutputObservation('Observation 1', url='', trigger_by_action=''),
        BrowserOutputObservation('Observation 2', url='', trigger_by_action=''),
        create_test_event('Event 3'),
        create_test_event('Event 4'),
        BrowserOutputObservation('Observation 3', url='', trigger_by_action=''),
        BrowserOutputObservation('Observation 4', url='', trigger_by_action=''),
    ]

    state = State()
    state.history = events

    result = condenser.condensed_history(state)

    assert len(result) == len(events)
    cnt = 4
    for event, condensed_event in zip(events, result):
        if isinstance(event, (BrowserOutputObservation, AgentCondensationObservation)):
            if cnt > attention_window:
                assert 'Content omitted' in str(condensed_event)
            else:
                assert event == condensed_event
            cnt -= 1
        else:
            assert event == condensed_event