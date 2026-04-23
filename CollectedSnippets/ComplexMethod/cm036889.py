def _validate_event_ordering(events: list) -> None:
    """Validate that envelope events appear in the correct positions."""
    assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"

    # First event must be response.created
    assert events[0].type == "response.created", (
        f"First event must be response.created, got {events[0].type}"
    )
    # Last event must be response.completed
    assert events[-1].type == "response.completed", (
        f"Last event must be response.completed, got {events[-1].type}"
    )

    # response.in_progress, if present, must be the second event
    in_progress_indices = [
        i for i, e in enumerate(events) if e.type == "response.in_progress"
    ]
    if in_progress_indices:
        assert in_progress_indices == [1], (
            f"response.in_progress must be the second event, "
            f"found at indices {in_progress_indices}"
        )

    # Exactly one created and one completed
    created_count = sum(1 for e in events if e.type == "response.created")
    completed_count = sum(1 for e in events if e.type == "response.completed")
    assert created_count == 1, (
        f"Expected exactly 1 response.created, got {created_count}"
    )
    assert completed_count == 1, (
        f"Expected exactly 1 response.completed, got {completed_count}"
    )