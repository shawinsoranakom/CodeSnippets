async def test_api_key_org_isolation_cross_org_visibility(
        self,
        async_session_with_users: AsyncSession,
    ):
        """Test end-to-end: conversation created via API key is visible in correct org.

        Simulates the full bug scenario:
        1. Create conversation via API key (bound to ORG1)
        2. User switches to ORG2
        3. User should NOT see the conversation in ORG2
        4. User switches back to ORG1
        5. User should see the conversation in ORG1
        """
        from dataclasses import dataclass

        @dataclass
        class MockUserAuth:
            user_id: str
            api_key_org_id: UUID | None = None

            async def get_user_id(self) -> str:
                return self.user_id

            def get_api_key_org_id(self) -> UUID | None:
                return self.api_key_org_id

        @dataclass
        class MockAuthUserContext:
            user_auth: MockUserAuth

            async def get_user_id(self) -> str | None:
                return await self.user_auth.get_user_id()

        # Step 1: Create conversation via API key bound to ORG1
        mock_user_auth = MockUserAuth(
            user_id=str(USER1_ID),
            api_key_org_id=ORG1_ID,
        )
        mock_context = MockAuthUserContext(user_auth=mock_user_auth)

        api_key_service = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=mock_context,
        )

        conv_id = uuid4()
        conv_info = AppConversationInfo(
            id=conv_id,
            created_by_user_id=str(USER1_ID),
            sandbox_id='sandbox_e2e_api_key',
            title='E2E API Key Conversation',
        )
        await api_key_service.save_app_conversation_info(conv_info)

        # Step 2: Switch user to ORG2 in browser session
        result = await async_session_with_users.execute(
            select(User).where(User.id == USER1_ID)
        )
        user_to_update = result.scalars().first()
        user_to_update.current_org_id = ORG2_ID
        await async_session_with_users.commit()
        async_session_with_users.expire_all()

        # Step 3: User in ORG2 should NOT see the conversation
        user_service_org2 = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )
        page_org2 = await user_service_org2.search_app_conversation_info()
        assert (
            len(page_org2.items) == 0
        ), 'User in ORG2 should not see conversation created via API key in ORG1'

        # Also verify get_app_conversation_info returns None
        conv_from_org2 = await user_service_org2.get_app_conversation_info(conv_id)
        assert (
            conv_from_org2 is None
        ), 'User in ORG2 should not access conversation from ORG1'

        # Step 4: Switch user back to ORG1
        result = await async_session_with_users.execute(
            select(User).where(User.id == USER1_ID)
        )
        user_to_update = result.scalars().first()
        user_to_update.current_org_id = ORG1_ID
        await async_session_with_users.commit()
        async_session_with_users.expire_all()

        # Step 5: User in ORG1 should see the conversation
        user_service_org1 = SaasSQLAppConversationInfoService(
            db_session=async_session_with_users,
            user_context=SpecifyUserContext(user_id=str(USER1_ID)),
        )
        page_org1 = await user_service_org1.search_app_conversation_info()
        assert (
            len(page_org1.items) == 1
        ), 'User in ORG1 should see conversation created via API key in ORG1'
        assert page_org1.items[0].id == conv_id
        assert page_org1.items[0].title == 'E2E API Key Conversation'

        # Also verify get_app_conversation_info works
        conv_from_org1 = await user_service_org1.get_app_conversation_info(conv_id)
        assert conv_from_org1 is not None
        assert conv_from_org1.id == conv_id