async def test_get_members_succeeds_returns_paginated_data(
        self, org_id, current_user_id, mock_org_member, requester_membership_owner
    ):
        """Test that successful retrieval returns paginated member data."""
        # Arrange
        from server.routes.org_models import OrgMemberPage

        with (
            patch(
                'server.services.org_member_service.OrgMemberStore.get_org_member',
                new_callable=AsyncMock,
            ) as mock_get_member,
            patch(
                'server.services.org_member_service.OrgMemberStore.get_org_members_paginated',
                new_callable=AsyncMock,
            ) as mock_get_paginated,
        ):
            mock_get_member.return_value = requester_membership_owner
            mock_get_paginated.return_value = ([mock_org_member], False)

            # Act
            success, error_code, data = await OrgMemberService.get_org_members(
                org_id=org_id,
                current_user_id=current_user_id,
                page_id=None,
                limit=100,
            )

            # Assert
            assert success is True
            assert error_code is None
            assert data is not None
            assert isinstance(data, OrgMemberPage)
            assert len(data.items) == 1
            assert data.current_page == 1
            assert data.per_page == 100
            assert data.items[0].user_id == str(current_user_id)
            assert data.items[0].email == 'test@example.com'
            assert data.items[0].role_id == 1
            assert data.items[0].role == 'owner'
            assert data.items[0].role_rank == 10
            assert data.items[0].status == 'active'