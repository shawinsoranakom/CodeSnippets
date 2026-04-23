async def test_search_sub_conversations_with_pagination(
        self,
        service: SQLAppConversationInfoService,
    ):
        """Test that include_sub_conversations works correctly with pagination."""
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

        # Create multiple sub-conversations
        sub_conversations = []
        for i in range(5):
            sub_info = AppConversationInfo(
                id=uuid4(),
                created_by_user_id='test_user_123',
                sandbox_id=f'sandbox_sub{i}',
                title=f'Sub Conversation {i}',
                parent_conversation_id=parent_id,
                created_at=datetime(2024, 1, 1, 13 + i, 0, 0, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 1, 13 + i, 30, 0, tzinfo=timezone.utc),
            )
            sub_conversations.append(sub_info)
            await service.save_app_conversation_info(sub_info)

        # Save parent
        await service.save_app_conversation_info(parent_info)

        # Search with include_sub_conversations=True and pagination
        page1 = await service.search_app_conversation_info(
            include_sub_conversations=True, limit=3
        )
        # Should return 3 items (1 parent + 2 sub-conversations)
        assert len(page1.items) == 3
        assert page1.next_page_id is not None

        # Get next page
        page2 = await service.search_app_conversation_info(
            include_sub_conversations=True, limit=3, page_id=page1.next_page_id
        )
        # Should return remaining items
        assert len(page2.items) == 3
        assert page2.next_page_id is None

        # Verify all conversations are present across pages
        all_ids = {item.id for item in page1.items} | {item.id for item in page2.items}
        assert parent_id in all_ids
        for sub_info in sub_conversations:
            assert sub_info.id in all_ids