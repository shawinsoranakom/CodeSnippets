def test_cache_page_creation(temp_dir: str):
    """Test that cache pages are created correctly when adding events."""
    file_store = get_file_store('local', temp_dir)
    event_stream = EventStream('cache_test', file_store)

    # Set a smaller cache size for testing
    event_stream.cache_size = 5

    # Add events up to the cache size threshold
    for i in range(10):
        event_stream.add_event(NullObservation(f'test{i}'), EventSource.AGENT)

    # Check that a cache page was created after adding the 5th event
    cache_filename = event_stream._get_filename_for_cache(0, 5)

    try:
        # Verify the content of the cache page
        cache_content = file_store.read(cache_filename)
        cache_exists = True
    except FileNotFoundError:
        cache_exists = False

    assert cache_exists, f'Cache file {cache_filename} should exist'

    # If cache exists, verify its content
    if cache_exists:
        cache_data = json.loads(cache_content)
        assert len(cache_data) == 5, 'Cache page should contain 5 events'

        # Verify each event in the cache
        for i, event_data in enumerate(cache_data):
            assert event_data['content'] == f'test{i}', (
                f"Event {i} content should be 'test{i}'"
            )