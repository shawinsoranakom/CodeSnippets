async def test_search_events_pagination_with_filters(
        self, service: FilesystemEventService
    ):
        """Test that pagination works correctly when combined with filters."""
        conversation_id = uuid4()

        # Create a mix of events
        token_events = [create_token_event() for _ in range(5)]
        pause_events = [create_pause_event() for _ in range(3)]

        for event in token_events + pause_events:
            await service.save_event(conversation_id, event)

        # Search only for token events with pagination
        page_limit = 2
        collected_ids = set()
        page_id = None

        while True:
            result = await service.search_events(
                conversation_id,
                kind__eq='TokenEvent',
                page_id=page_id,
                limit=page_limit,
            )

            for item in result.items:
                assert item.kind == 'TokenEvent'
                collected_ids.add(item.id)

            if result.next_page_id is None:
                break
            page_id = result.next_page_id

        # Should have found all 5 token events
        assert len(collected_ids) == 5