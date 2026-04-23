async def test_persist_org_with_owner_success(async_session_maker, mock_litellm_api):
    """
    GIVEN: Valid org and org_member entities
    WHEN: persist_org_with_owner is called
    THEN: Both entities are persisted in a single transaction and org is returned
    """
    # Arrange
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    # Create user and role first
    async with async_session_maker() as session:
        user = User(id=user_id, current_org_id=org_id)
        role = Role(id=1, name='owner', rank=1)
        session.add(user)
        session.add(role)
        await session.commit()

    org = Org(
        id=org_id,
        name='Test Organization',
        contact_name='John Doe',
        contact_email='john@example.com',
    )

    org_member = OrgMember(
        org_id=org_id,
        user_id=user_id,
        role_id=1,
        status='active',
        llm_api_key='test-api-key-123',
    )

    # Act
    with patch('storage.org_store.a_session_maker', async_session_maker):
        result = await OrgStore.persist_org_with_owner(org, org_member)

    # Assert
    assert result is not None
    assert result.id == org_id
    assert result.name == 'Test Organization'

    # Verify both entities were persisted
    async with async_session_maker() as session:
        persisted_org = await session.get(Org, org_id)
        assert persisted_org is not None
        assert persisted_org.name == 'Test Organization'

        result = await session.execute(
            select(OrgMember).filter_by(org_id=org_id, user_id=user_id)
        )
        persisted_member = result.scalars().first()
        assert persisted_member is not None
        assert persisted_member.status == 'active'
        assert persisted_member.role_id == 1