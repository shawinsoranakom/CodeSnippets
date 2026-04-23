def test_get_matching_events_source_filter(temp_dir: str):
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('abc', file_store)

    event_stream.add_event(NullObservation('test1'), EventSource.AGENT)
    event_stream.add_event(NullObservation('test2'), EventSource.ENVIRONMENT)
    event_stream.add_event(NullObservation('test3'), EventSource.AGENT)

    # Filter by AGENT source
    events = event_stream.get_matching_events(source='agent')
    assert len(events) == 2
    assert all(
        isinstance(e, NullObservation) and e.source == EventSource.AGENT for e in events
    )

    # Filter by ENVIRONMENT source
    events = event_stream.get_matching_events(source='environment')
    assert len(events) == 1
    assert (
        isinstance(events[0], NullObservation)
        and events[0].source == EventSource.ENVIRONMENT
    )

    # Test that source comparison works correctly with None source
    null_source_event = NullObservation('test4')
    event_stream.add_event(null_source_event, EventSource.AGENT)
    event = event_stream.get_event(event_stream.get_latest_event_id())
    event._source = None  # type: ignore

    # Update the serialized version
    data = event_to_dict(event)
    event_stream.file_store.write(
        event_stream._get_filename_for_id(event.id, event_stream.user_id),
        json.dumps(data),
    )

    # Verify that source comparison works correctly
    assert EventFilter(source='agent').exclude(event)
    assert EventFilter(source=None).include(event)

    # Filter by AGENT source again
    events = event_stream.get_matching_events(source='agent')
    assert len(events) == 2