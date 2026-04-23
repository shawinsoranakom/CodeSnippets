async def test_search_sub_conversations_with_filters(
        self,
        service: SQLAppConversationInfoService,
    ):
        """Test that include_sub_conversations works correctly with other filters."""
        # Create a parent conversation
        parent_id = uuid4()
        parent_info = AppConversationInfo(
            id=parent_id,
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_parent',
            title='Parent Conversation',
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        )

        # Create sub-conversations with different titles
        sub_info_1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub1',
            title='Sub Conversation Alpha',
            parent_conversation_id=parent_id,
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
        )

        sub_info_2 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub2',
            title='Sub Conversation Beta',
            parent_conversation_id=parent_id,
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        )

        # Save all conversations
        await service.save_app_conversation_info(parent_info)
        await service.save_app_conversation_info(sub_info_1)
        await service.save_app_conversation_info(sub_info_2)

        # Search with title filter and include_sub_conversations=False (default)
        page = await service.search_app_conversation_info(title__contains='Alpha')
        # Should only find parent if it matches, but parent doesn't have "Alpha"
        # So should find nothing or only sub if we include them
        assert len(page.items) == 0

        # Search with title filter and include_sub_conversations=True
        page = await service.search_app_conversation_info(
            title__contains='Alpha', include_sub_conversations=True
        )
        # Should find the sub-conversation with "Alpha" in title
        assert len(page.items) == 1
        assert page.items[0].title == 'Sub Conversation Alpha'
        assert page.items[0].parent_conversation_id == parent_id

        # Search with title filter for "Parent" and include_sub_conversations=True
        page = await service.search_app_conversation_info(
            title__contains='Parent', include_sub_conversations=True
        )
        # Should find the parent conversation
        assert len(page.items) == 1
        assert page.items[0].title == 'Parent Conversation'
        assert page.items[0].parent_conversation_id is None