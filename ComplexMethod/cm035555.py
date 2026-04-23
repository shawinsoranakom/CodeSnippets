async def test_search_events_pagination_iterates_all_events(
        self, service: FilesystemEventService
    ):
        """Test that pagination correctly iterates through all events without duplicates.

        This test verifies the fix for a bug where pagination was applied to 'paths'
        instead of 'items', causing all events to be returned on every page.
        """
        conversation_id = uuid4()
        total_events = 10
        page_limit = 3

        # Create events and track their IDs
        created_event_ids = set()
        for _ in range(total_events):
            event = create_token_event()
            created_event_ids.add(event.id)
            await service.save_event(conversation_id, event)

        # Iterate through all pages and collect event IDs
        collected_event_ids = set()
        page_id = None
        page_count = 0

        while True:
            result = await service.search_events(
                conversation_id, page_id=page_id, limit=page_limit
            )
            page_count += 1

            for item in result.items:
                # Verify no duplicates - this would fail with the old buggy code
                assert item.id not in collected_event_ids, (
                    f'Duplicate event {item.id} found on page {page_count}'
                )
                collected_event_ids.add(item.id)

            if result.next_page_id is None:
                break
            page_id = result.next_page_id

        # Verify we got all events exactly once
        assert collected_event_ids == created_event_ids
        assert len(collected_event_ids) == total_events

        # With 10 events and limit of 3, we should have 4 pages (3+3+3+1)
        expected_pages = (total_events + page_limit - 1) // page_limit
        assert page_count == expected_pages