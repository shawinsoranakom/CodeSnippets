async def test_get_me_success_returns_me_response(
        self, org_id, current_user_id, mock_org_member, mock_user, owner_role
    ):
        """GIVEN: User is a member of the organization
        WHEN: get_me is called
        THEN: Returns MeResponse with user's membership data
        """
        # Arrange
        with (
            patch(
                'server.services.org_member_service.OrgMemberStore.get_org_member',
                new_callable=AsyncMock,
            ) as mock_get_member,
            patch(
                'server.services.org_member_service.RoleStore.get_role_by_id',
                new_callable=AsyncMock,
            ) as mock_get_role,
            patch(
                'server.services.org_member_service.UserStore.get_user_by_id',
                new_callable=AsyncMock,
            ) as mock_get_user,
        ):
            mock_get_member.return_value = mock_org_member
            mock_get_role.return_value = owner_role
            mock_get_user.return_value = mock_user

            # Act
            result = await OrgMemberService.get_me(org_id, current_user_id)

            # Assert
            assert isinstance(result, MeResponse)
            assert result.org_id == str(org_id)
            assert result.user_id == str(current_user_id)
            assert result.email == 'test@example.com'
            assert result.role == 'owner'
            assert result.agent_settings_diff['llm']['model'] == 'gpt-4'
            assert result.conversation_settings_diff['max_iterations'] == 50
            assert result.status == 'active'