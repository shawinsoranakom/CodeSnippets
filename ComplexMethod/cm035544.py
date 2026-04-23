async def test_search_conversation_info_pagination(
        self,
        service: SQLAppConversationInfoService,
        multiple_conversation_infos: list[AppConversationInfo],
    ):
        """Test search with pagination."""
        # Save all conversation infos
        for info in multiple_conversation_infos:
            await service.save_app_conversation_info(info)

        # Get first page with limit 2
        page1 = await service.search_app_conversation_info(limit=2)
        assert len(page1.items) == 2
        assert page1.next_page_id is not None

        # Get second page
        page2 = await service.search_app_conversation_info(
            limit=2, page_id=page1.next_page_id
        )
        assert len(page2.items) == 2
        assert page2.next_page_id is not None

        # Get third page
        page3 = await service.search_app_conversation_info(
            limit=2, page_id=page2.next_page_id
        )
        assert len(page3.items) == 1  # Only 1 remaining
        assert page3.next_page_id is None

        # Verify no overlap between pages
        all_ids = set()
        for page in [page1, page2, page3]:
            for item in page.items:
                assert item.id not in all_ids  # No duplicates
                all_ids.add(item.id)

        assert len(all_ids) == len(multiple_conversation_infos)