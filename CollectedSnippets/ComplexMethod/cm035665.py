def test_search_events_limit_with_complex_filters(temp_dir: str):
    """Test the interaction between limit and various filter combinations in search_events."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    # Add events with different sources and types
    event_stream.add_event(NullAction(), EventSource.AGENT)  # id 0
    event_stream.add_event(NullObservation('test1'), EventSource.AGENT)  # id 1
    event_stream.add_event(MessageAction(content='hello'), EventSource.USER)  # id 2
    event_stream.add_event(NullObservation('test2'), EventSource.ENVIRONMENT)  # id 3
    event_stream.add_event(NullAction(), EventSource.AGENT)  # id 4
    event_stream.add_event(MessageAction(content='world'), EventSource.USER)  # id 5
    event_stream.add_event(NullObservation('hello world'), EventSource.AGENT)  # id 6

    # Test limit with type filter
    events = list(
        event_stream.search_events(
            filter=EventFilter(include_types=(NullAction,)), limit=1
        )
    )
    assert len(events) == 1
    assert isinstance(events[0], NullAction)
    assert events[0].id == 0

    # Test limit with source filter
    events = list(
        event_stream.search_events(filter=EventFilter(source='user'), limit=1)
    )
    assert len(events) == 1
    assert events[0].source == EventSource.USER
    assert events[0].id == 2

    # Test limit with query filter
    events = list(
        event_stream.search_events(filter=EventFilter(query='hello'), limit=2)
    )
    assert len(events) == 2
    assert [e.id for e in events] == [2, 6]

    # Test limit with combined filters
    events = list(
        event_stream.search_events(
            filter=EventFilter(source='agent', include_types=(NullObservation,)),
            limit=1,
        )
    )
    assert len(events) == 1
    assert isinstance(events[0], NullObservation)
    assert events[0].source == EventSource.AGENT
    assert events[0].id == 1

    # Test limit with reverse and filter
    events = list(
        event_stream.search_events(
            filter=EventFilter(source='agent'), reverse=True, limit=2
        )
    )
    assert len(events) == 2
    assert [e.id for e in events] == [6, 4]