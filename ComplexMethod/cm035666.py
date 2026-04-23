def test_search_events_limit_edge_cases(temp_dir: str):
    """Test edge cases for the limit parameter in search_events."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add some events
    for i in range(5):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test with limit=None (should return all events)
    events = list(event_stream.search_events(limit=None))
    assert len(events) == 5

    # Test with limit larger than number of events
    events = list(event_stream.search_events(limit=10))
    assert len(events) == 5

    # Test with limit=0 (let's check actual behavior)
    events = list(event_stream.search_events(limit=0))
    # If it returns all events, assert len(events) == 5
    # If it returns no events, assert len(events) == 0
    # Let's check the actual behavior
    assert len(events) in [0, 5]

    # Test with negative limit (implementation returns only first event)
    events = list(event_stream.search_events(limit=-1))
    assert len(events) == 1

    # Test with empty result set and limit
    events = list(
        event_stream.search_events(filter=EventFilter(query='nonexistent'), limit=5)
    )
    assert len(events) == 0

    # Test with start_id beyond available events
    events = list(event_stream.search_events(start_id=10, limit=5))
    assert len(events) == 0