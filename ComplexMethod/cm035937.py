async def test_search_by_sandbox_id(
        self,
        async_session_with_users: AsyncSession,
    ):
        """Test searching conversations by exact sandbox_id match with SAAS user filtering."""
        # Create service for user1
        user1_service = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )

        # Create conversations with different sandbox IDs for user1
        conv1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_alpha',
            title='Conversation Alpha',
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        )
        conv2 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_beta',
            title='Conversation Beta',
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
        )
        conv3 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_alpha',
            title='Conversation Gamma',
            created_at=datetime(2024, 1, 1, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        )

        # Save all conversations
        await user1_service.save_app_conversation_info(conv1)
        await user1_service.save_app_conversation_info(conv2)
        await user1_service.save_app_conversation_info(conv3)

        # Search for sandbox_alpha - should return 2 conversations
        page = await user1_service.search_app_conversation_info(
            sandbox_id__eq='sandbox_alpha'
        )
        assert len(page.items) == 2
        sandbox_ids = {item.sandbox_id for item in page.items}
        assert sandbox_ids == {'sandbox_alpha'}
        conversation_ids = {item.id for item in page.items}
        assert conv1.id in conversation_ids
        assert conv3.id in conversation_ids

        # Search for sandbox_beta - should return 1 conversation
        page = await user1_service.search_app_conversation_info(
            sandbox_id__eq='sandbox_beta'
        )
        assert len(page.items) == 1
        assert page.items[0].id == conv2.id

        # Search for non-existent sandbox - should return 0 conversations
        page = await user1_service.search_app_conversation_info(
            sandbox_id__eq='sandbox_nonexistent'
        )
        assert len(page.items) == 0