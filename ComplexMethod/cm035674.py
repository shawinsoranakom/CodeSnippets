def test_recent_events_condenser():
    """Test that RecentEventsCondensers keep just the most recent events."""
    events = [
        create_test_event('Event 1'),
        create_test_event('Event 2'),
        create_test_event('Event 3'),
        create_test_event('Event 4'),
        create_test_event('Event 5'),
    ]

    state = State()
    state.history = events

    # If the max_events are larger than the number of events, equivalent to a NoOpCondenser.
    condenser = RecentEventsCondenser(max_events=len(events))
    result = condenser.condensed_history(state)

    assert result == View(events=events)

    # If the max_events are smaller than the number of events, only keep the last few.
    max_events = 3
    condenser = RecentEventsCondenser(max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'  # kept from keep_first
    assert result[1]._message == 'Event 4'  # kept from max_events
    assert result[2]._message == 'Event 5'  # kept from max_events

    # If the keep_first flag is set, the first event will always be present.
    keep_first = 1
    max_events = 2
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'
    assert result[1]._message == 'Event 5'

    # We should be able to keep more of the initial events.
    keep_first = 2
    max_events = 3
    condenser = RecentEventsCondenser(keep_first=keep_first, max_events=max_events)
    result = condenser.condensed_history(state)

    assert len(result) == max_events
    assert result[0]._message == 'Event 1'  # kept from keep_first
    assert result[1]._message == 'Event 2'  # kept from keep_first
    assert result[2]._message == 'Event 5'