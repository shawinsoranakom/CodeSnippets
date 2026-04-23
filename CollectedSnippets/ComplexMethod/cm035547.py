async def test_search_multiple_parents_with_sub_conversations(
        self,
        service: SQLAppConversationInfoService,
    ):
        """Test search with multiple parent conversations and their sub-conversations."""
        # Create first parent conversation
        parent1_id = uuid4()
        parent1_info = AppConversationInfo(
            id=parent1_id,
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_parent1',
            title='Parent 1',
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        )

        # Create second parent conversation
        parent2_id = uuid4()
        parent2_info = AppConversationInfo(
            id=parent2_id,
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_parent2',
            title='Parent 2',
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
        )

        # Create sub-conversations for parent1
        sub1_1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub1_1',
            title='Sub 1-1',
            parent_conversation_id=parent1_id,
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        )

        # Create sub-conversations for parent2
        sub2_1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id='test_user_123',
            sandbox_id='sandbox_sub2_1',
            title='Sub 2-1',
            parent_conversation_id=parent2_id,
            created_at=datetime(2024, 1, 1, 15, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 15, 30, 0, tzinfo=timezone.utc),
        )

        # Save all conversations
        await service.save_app_conversation_info(parent1_info)
        await service.save_app_conversation_info(parent2_info)
        await service.save_app_conversation_info(sub1_1)
        await service.save_app_conversation_info(sub2_1)

        # Search without include_sub_conversations (default False)
        page = await service.search_app_conversation_info()
        # Should only return the 2 parent conversations
        assert len(page.items) == 2
        conversation_ids = {item.id for item in page.items}
        assert parent1_id in conversation_ids
        assert parent2_id in conversation_ids
        assert sub1_1.id not in conversation_ids
        assert sub2_1.id not in conversation_ids

        # Search with include_sub_conversations=True
        page = await service.search_app_conversation_info(
            include_sub_conversations=True
        )
        # Should return all 4 conversations (2 parents + 2 sub-conversations)
        assert len(page.items) == 4
        conversation_ids = {item.id for item in page.items}
        assert parent1_id in conversation_ids
        assert parent2_id in conversation_ids
        assert sub1_1.id in conversation_ids
        assert sub2_1.id in conversation_ids