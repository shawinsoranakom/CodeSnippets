def _assert_events_equal_allow_superset_metadata(
    events: Sequence[Mapping[str, Any]], expected: Sequence[Mapping[str, Any]]
) -> None:
    """Assert that the events are equal."""
    assert len(events) == len(expected)
    for i, (event, expected_event) in enumerate(zip(events, expected, strict=False)):
        # we want to allow a superset of metadata on each
        event_with_edited_metadata = {
            k: (
                v
                if k != "metadata"
                else {
                    metadata_k: metadata_v
                    for metadata_k, metadata_v in v.items()
                    if metadata_k in expected_event["metadata"]
                }
            )
            for k, v in event.items()
        }
        assert event_with_edited_metadata == expected_event, f"Event {i} did not match."