async def test_sandbox_id_filter_respects_user_isolation(
        self,
        async_session_with_users: AsyncSession,
    ):
        """Test that sandbox_id filter respects user isolation in SAAS environment."""
        # Create services for both users
        user1_service = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )
        user2_service = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER2_ID)),
        )

        # Create conversation with same sandbox_id for both users
        shared_sandbox_id = 'sandbox_shared'

        conv_user1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id=shared_sandbox_id,
            title='User1 Conversation',
            created_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        )
        conv_user2 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER2_ID),
            sandbox_id=shared_sandbox_id,
            title='User2 Conversation',
            created_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
        )

        # Save conversations
        await user1_service.save_app_conversation_info(conv_user1)
        await user2_service.save_app_conversation_info(conv_user2)

        # User1 should only see their own conversation with this sandbox_id
        page = await user1_service.search_app_conversation_info(
            sandbox_id__eq=shared_sandbox_id
        )
        assert len(page.items) == 1
        assert page.items[0].id == conv_user1.id
        assert page.items[0].title == 'User1 Conversation'

        # User2 should only see their own conversation with this sandbox_id
        page = await user2_service.search_app_conversation_info(
            sandbox_id__eq=shared_sandbox_id
        )
        assert len(page.items) == 1
        assert page.items[0].id == conv_user2.id
        assert page.items[0].title == 'User2 Conversation'

        # Count should also respect user isolation
        count = await user1_service.count_app_conversation_info(
            sandbox_id__eq=shared_sandbox_id
        )
        assert count == 1

        count = await user2_service.count_app_conversation_info(
            sandbox_id__eq=shared_sandbox_id
        )
        assert count == 1