async def test_search_conversation_info_sorting(
        self,
        service: SQLAppConversationInfoService,
        multiple_conversation_infos: list[AppConversationInfo],
    ):
        """Test search with different sort orders."""
        # Save all conversation infos
        for info in multiple_conversation_infos:
            await service.save_app_conversation_info(info)

        # Test created_at ascending
        page = await service.search_app_conversation_info(
            sort_order=AppConversationSortOrder.CREATED_AT
        )
        created_times = [item.created_at for item in page.items]
        assert created_times == sorted(created_times)

        # Test created_at descending (default)
        page = await service.search_app_conversation_info(
            sort_order=AppConversationSortOrder.CREATED_AT_DESC
        )
        created_times = [item.created_at for item in page.items]
        assert created_times == sorted(created_times, reverse=True)

        # Test title ascending
        page = await service.search_app_conversation_info(
            sort_order=AppConversationSortOrder.TITLE
        )
        titles = [item.title for item in page.items]
        assert titles == sorted(titles)

        # Test title descending
        page = await service.search_app_conversation_info(
            sort_order=AppConversationSortOrder.TITLE_DESC
        )
        titles = [item.title for item in page.items]
        assert titles == sorted(titles, reverse=True)