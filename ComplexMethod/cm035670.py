def test_view_inserts_summary() -> None:
    """Tests that views insert a summary observation at the specified offset."""
    for offset in range(5):
        events: list[Event] = [
            *[MessageAction(content=f'Event {i}') for i in range(5)],
            CondensationAction(
                forgotten_event_ids=[], summary='My Summary', summary_offset=offset
            ),
        ]
        set_ids(events)
        view = View.from_events(events)

        assert len(view) == 6  # 5 message events + 1 summary observation
        for index, event in enumerate(view):
            print(index, event.content)
            if index == offset:
                assert isinstance(event, AgentCondensationObservation)
                assert event.content == 'My Summary'

            # Events before where the summary is inserted will have content
            # matching their index.
            elif index < offset:
                assert isinstance(event, MessageAction)
                assert event.content == f'Event {index}'

            # Events after where the summary is inserted will be offset by one
            # from the original list.
            else:
                assert isinstance(event, MessageAction)
                assert event.content == f'Event {index - 1}'