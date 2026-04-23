def test_condensation_request_always_removed_from_view() -> None:
    """Test that CondensationRequestAction is always removed from the view regardless of unhandled status."""
    # Test case 1: Unhandled request
    events_unhandled: list[Event] = [
        MessageAction(content='Event 0'),
        CondensationRequestAction(),
        MessageAction(content='Event 1'),
    ]
    set_ids(events_unhandled)
    view_unhandled = View.from_events(events_unhandled)

    assert view_unhandled.unhandled_condensation_request is True
    assert len(view_unhandled) == 2  # Only MessageActions
    for event in view_unhandled:
        assert not isinstance(event, CondensationRequestAction)

    # Test case 2: Handled request
    events_handled: list[Event] = [
        MessageAction(content='Event 0'),
        CondensationRequestAction(),
        MessageAction(content='Event 1'),
        CondensationAction(forgotten_event_ids=[]),
        MessageAction(content='Event 2'),
    ]
    set_ids(events_handled)
    view_handled = View.from_events(events_handled)

    assert view_handled.unhandled_condensation_request is False
    assert len(view_handled) == 3  # Only MessageActions
    for event in view_handled:
        assert not isinstance(event, CondensationRequestAction)
        assert not isinstance(event, CondensationAction)