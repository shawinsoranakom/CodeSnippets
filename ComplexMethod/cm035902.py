async def test_get_org_members_paginated_with_offset(async_session_maker):
    """Test pagination with offset skips correct number of items."""
    # Arrange
    async with async_session_maker() as session:
        org = Org(name='test-org')
        session.add(org)
        await session.flush()

        role = Role(name='admin', rank=1)
        session.add(role)
        await session.flush()

        # Create 10 users
        users = [
            User(id=uuid.uuid4(), current_org_id=org.id, email=f'user{i}@example.com')
            for i in range(10)
        ]
        session.add_all(users)
        await session.flush()

        # Create org members
        org_members = [
            OrgMember(
                org_id=org.id,
                user_id=user.id,
                role_id=role.id,
                llm_api_key=f'test-key-{i}',
                status='active',
            )
            for i, user in enumerate(users)
        ]
        session.add_all(org_members)
        await session.commit()
        org_id = org.id

    # Act - Get first page
    with patch('storage.org_member_store.a_session_maker', async_session_maker):
        first_page, has_more_first = await OrgMemberStore.get_org_members_paginated(
            org_id=org_id, offset=0, limit=3
        )

        # Get second page
        second_page, has_more_second = await OrgMemberStore.get_org_members_paginated(
            org_id=org_id, offset=3, limit=3
        )

        # Assert
        assert len(first_page) == 3
        assert has_more_first is True
        assert len(second_page) == 3
        assert has_more_second is True

        # Verify no overlap between pages
        first_user_ids = {member.user_id for member in first_page}
        second_user_ids = {member.user_id for member in second_page}
        assert first_user_ids.isdisjoint(second_user_ids)