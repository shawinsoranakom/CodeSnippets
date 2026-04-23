async def test_get_org_info_returns_correct_data_for_owner(
        self, async_session_maker, user_id, org_id
    ):
        """Test that get_org_info returns correct data for an owner role."""
        # Set up test data
        owner_role = await create_role(async_session_maker, 'owner', 1)
        await create_org(async_session_maker, org_id, 'Test Organization')
        await create_user(async_session_maker, user_id, org_id)
        await create_org_member(async_session_maker, org_id, user_id, owner_role.id)

        # Create SaasUserAuth instance
        user_auth = SaasUserAuth(
            user_id=user_id,
            refresh_token=SecretStr('mock_refresh_token'),
        )

        # Patch the global a_session_maker in all stores that use it
        with (
            patch('storage.user_store.a_session_maker', async_session_maker),
            patch('storage.org_store.a_session_maker', async_session_maker),
            patch('storage.org_member_store.a_session_maker', async_session_maker),
            patch('storage.role_store.a_session_maker', async_session_maker),
        ):
            org_info = await user_auth.get_org_info()

        assert org_info is not None
        assert org_info['org_id'] == str(org_id)
        assert org_info['org_name'] == 'Test Organization'
        assert org_info['role'] == 'owner'
        assert isinstance(org_info['permissions'], list)
        # Owner should have many permissions
        assert len(org_info['permissions']) > 0
        assert 'manage_secrets' in org_info['permissions']