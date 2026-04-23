def test_search_events_limit(temp_dir: str):
    """Test that the search_events method correctly applies the limit parameter."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add 10 events
    for i in range(10):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test with no limit (should return all events)
    events = list(event_stream.search_events())
    assert len(events) == 10

    # Test with limit=5 (should return first 5 events)
    events = list(event_stream.search_events(limit=5))
    assert len(events) == 5
    assert all(isinstance(e, NullObservation) for e in events)
    assert [e.content for e in events] == ['test0', 'test1', 'test2', 'test3', 'test4']

    # Test with limit=3 and start_id=5 (should return 3 events starting from ID 5)
    events = list(event_stream.search_events(start_id=5, limit=3))
    assert len(events) == 3
    assert [e.content for e in events] == ['test5', 'test6', 'test7']

    # Test with limit and reverse=True (should return events in reverse order)
    events = list(event_stream.search_events(reverse=True, limit=4))
    assert len(events) == 4
    assert [e.content for e in events] == ['test9', 'test8', 'test7', 'test6']

    # Test with limit and filter (should apply limit after filtering)
    # Add some events with different content for filtering
    event_stream.add_event(NullObservation('filter_me'), EventSource.AGENT)
    event_stream.add_event(NullObservation('filter_me_too'), EventSource.AGENT)

    events = list(
        event_stream.search_events(filter=EventFilter(query='filter'), limit=1)
    )
    assert len(events) == 1
    assert events[0].content == 'filter_me'