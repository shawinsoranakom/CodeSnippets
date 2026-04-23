async def test_search_includes_sub_conversations_when_flag_true(
        self,
        service: SQLAppConversationInfoService,
    ):
        """Test that search includes sub-conversations when include_sub_conversations=True."""
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

        # Create sub-conversations
        sub_info_1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub1',
            title='Sub Conversation 1',
            parent_conversation_id=parent_id,
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
        )

        sub_info_2 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub2',
            title='Sub Conversation 2',
            parent_conversation_id=parent_id,
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        )

        # Save all conversations
        await service.save_app_conversation_info(parent_info)
        await service.save_app_conversation_info(sub_info_1)
        await service.save_app_conversation_info(sub_info_2)

        # Search with include_sub_conversations=True
        page = await service.search_app_conversation_info(
            include_sub_conversations=True
        )

        # Should return all conversations (1 parent + 2 sub-conversations)
        assert len(page.items) == 3

        # Verify all conversations are present
        conversation_ids = {item.id for item in page.items}
        assert parent_id in conversation_ids
        assert sub_info_1.id in conversation_ids
        assert sub_info_2.id in conversation_ids

        # Verify parent conversation has no parent_conversation_id
        parent_item = next(item for item in page.items if item.id == parent_id)
        assert parent_item.parent_conversation_id is None

        # Verify sub-conversations have parent_conversation_id set
        sub_item_1 = next(item for item in page.items if item.id == sub_info_1.id)
        assert sub_item_1.parent_conversation_id == parent_id

        sub_item_2 = next(item for item in page.items if item.id == sub_info_2.id)
        assert sub_item_2.parent_conversation_id == parent_id