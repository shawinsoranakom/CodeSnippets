async def test_same_user_org_switching_isolation(
        self,
        async_session_with_users: AsyncSession,
    ):
        """Test that the same user switching orgs cannot see conversations from other orgs.

        This tests the actual bug scenario: a user creates a conversation in org1,
        then switches to org2, and should NOT see org1's conversations.
        """
        # Create service for user1 in org1
        user1_service_org1 = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )

        # Create a conversation while user is in org1
        conv_in_org1 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_org1',
            title='Conversation in Org 1',
        )
        await user1_service_org1.save_app_conversation_info(conv_in_org1)

        # Verify user can see the conversation in org1
        page_in_org1 = await user1_service_org1.search_app_conversation_info()
        assert len(page_in_org1.items) == 1
        assert page_in_org1.items[0].title == 'Conversation in Org 1'

        # Simulate user switching to org2 by updating current_org_id using ORM
        result = await async_session_with_users.execute(
            select(User).where(User.id == USER1_ID)
        )
        user_to_update = result.scalars().first()
        user_to_update.current_org_id = ORG2_ID
        await async_session_with_users.commit()
        # Clear SQLAlchemy's identity map cache to simulate a new request
        async_session_with_users.expire_all()

        # Create new service instance (simulating a new request after org switch)
        user1_service_org2 = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )

        # User should NOT see org1's conversations after switching to org2
        page_in_org2 = await user1_service_org2.search_app_conversation_info()
        assert (
            len(page_in_org2.items) == 0
        ), 'User should not see conversations from org1 after switching to org2'

        # User should not be able to get the specific conversation from org1
        conv_from_org2 = await user1_service_org2.get_app_conversation_info(
            conv_in_org1.id
        )
        assert (
            conv_from_org2 is None
        ), 'User should not be able to access org1 conversation from org2'

        # Now create a conversation in org2
        conv_in_org2 = AppConversationInfo(
            id=uuid4(),
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_org2',
            title='Conversation in Org 2',
        )
        await user1_service_org2.save_app_conversation_info(conv_in_org2)

        # User should only see org2's conversation
        page_in_org2_after = await user1_service_org2.search_app_conversation_info()
        assert len(page_in_org2_after.items) == 1
        assert page_in_org2_after.items[0].title == 'Conversation in Org 2'

        # Switch back to org1 and verify isolation works both ways
        result = await async_session_with_users.execute(
            select(User).where(User.id == USER1_ID)
        )
        user_to_update = result.scalars().first()
        user_to_update.current_org_id = ORG1_ID
        await async_session_with_users.commit()
        async_session_with_users.expire_all()

        user1_service_back_to_org1 = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )

        # User should only see org1's conversation now
        page_back_in_org1 = (
            await user1_service_back_to_org1.search_app_conversation_info()
        )
        assert len(page_back_in_org1.items) == 1
        assert page_back_in_org1.items[0].title == 'Conversation in Org 1'