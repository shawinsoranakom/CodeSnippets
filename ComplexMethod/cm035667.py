def test_cache_page_partial_retrieval(temp_dir: str):
    """Test retrieving events with start_id and end_id parameters using the cache."""
    file_store = get_file_store('local', temp_dir)

    # Create an event stream with a small cache size
    event_stream = EventStream('partial_test', file_store)
    event_stream.cache_size = 5

    # Add events
    for i in range(20):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Test retrieving a subset of events that spans multiple cache pages
    events = list(event_stream.get_events(start_id=3, end_id=12))

    # Verify we got a reasonable number of events
    assert len(events) >= 8, 'Should retrieve most events in the range'

    # Verify the events we did get are in the correct order
    for i, event in enumerate(events):
        expected_content = f'test{i + 3}'
        assert event.content == expected_content, (
            f"Event {i} content should be '{expected_content}'"
        )

    # Test retrieving events in reverse order
    reverse_events = list(event_stream.get_events(start_id=3, end_id=12, reverse=True))

    # Verify we got a reasonable number of events in reverse
    assert len(reverse_events) >= 8, 'Should retrieve most events in reverse'

    # Check the first few events to ensure they're in reverse order
    if len(reverse_events) >= 3:
        assert reverse_events[0].content.startswith('test1'), (
            'First reverse event should be near the end of the range'
        )
        assert int(reverse_events[0].content[4:]) > int(
            reverse_events[1].content[4:]
        ), 'Events should be in descending order'