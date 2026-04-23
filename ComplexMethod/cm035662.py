def test_get_matching_events_pagination(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add 5 events
    for i in range(5):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test limit
    events = event_stream.get_matching_events(limit=3)
    assert len(events) == 3

    # Test start_id
    events = event_stream.get_matching_events(start_id=2)
    assert len(events) == 3
    assert isinstance(events[0], NullObservation) and events[0].content == 'test2'

    # Test combination of start_id and limit
    events = event_stream.get_matching_events(start_id=1, limit=2)
    assert len(events) == 2
    assert isinstance(events[0], NullObservation) and events[0].content == 'test1'
    assert isinstance(events[1], NullObservation) and events[1].content == 'test2'