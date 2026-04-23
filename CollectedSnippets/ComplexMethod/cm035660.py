def test_get_matching_events_type_filter(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add mixed event types
    event_stream.add_event(NullAction(), EventSource.AGENT)
    event_stream.add_event(NullObservation('test'), EventSource.AGENT)
    event_stream.add_event(NullAction(), EventSource.AGENT)
    event_stream.add_event(MessageAction(content='test'), EventSource.AGENT)

    # Filter by NullAction
    events = event_stream.get_matching_events(event_types=(NullAction,))
    assert len(events) == 2
    assert all(isinstance(e, NullAction) for e in events)

    # Filter by NullObservation
    events = event_stream.get_matching_events(event_types=(NullObservation,))
    assert len(events) == 1
    assert (
        isinstance(events[0], NullObservation)
        and events[0].observation == ObservationType.NULL
    )

    # Filter by NullAction and MessageAction
    events = event_stream.get_matching_events(event_types=(NullAction, MessageAction))
    assert len(events) == 3

    # Filter in reverse
    events = event_stream.get_matching_events(reverse=True, limit=3)
    assert len(events) == 3
    assert isinstance(events[0], MessageAction) and events[0].content == 'test'
    assert isinstance(events[2], NullObservation) and events[2].content == 'test'