async def test_persist_org_with_owner_with_multiple_fields(
    async_session_maker, mock_litellm_api
):
    """
    GIVEN: Org with multiple optional fields populated
    WHEN: persist_org_with_owner is called
    THEN: All fields are persisted correctly
    """
    # Arrange
    org_id = uuid.uuid4()
    user_id = uuid.uuid4()

    async with async_session_maker() as session:
        user = User(id=user_id, current_org_id=org_id)
        role = Role(id=1, name='owner', rank=1)
        session.add(user)
        session.add(role)
        await session.commit()

    org = Org(
        id=org_id,
        name='Complex Org',
        contact_name='Alice Smith',
        contact_email='alice@example.com',
        agent_settings=AgentSettings(agent='CodeActAgent'),
        billing_margin=0.15,
    )

    org_member = OrgMember(
        org_id=org_id,
        user_id=user_id,
        role_id=1,
        status='active',
        llm_api_key='test-key',
        agent_settings_diff={
            'llm': {'model': 'gpt-4'},
        },
        conversation_settings_diff={
            'max_iterations': 100,
        },
    )

    # Act
    with patch('storage.org_store.a_session_maker', async_session_maker):
        result = await OrgStore.persist_org_with_owner(org, org_member)

    # Assert
    assert result.name == 'Complex Org'
    assert result.agent_settings['agent'] == 'CodeActAgent'
    assert result.billing_margin == 0.15

    # Verify persistence
    async with async_session_maker() as session:
        persisted_org = await session.get(Org, org_id)
        assert persisted_org.agent_settings['agent'] == 'CodeActAgent'
        assert persisted_org.billing_margin == 0.15

        result_query = await session.execute(
            select(OrgMember).filter_by(org_id=org_id, user_id=user_id)
        )
        persisted_member = result_query.scalars().first()
        assert persisted_member.conversation_settings_diff['max_iterations'] == 100
        assert persisted_member.agent_settings_diff['llm']['model'] == 'gpt-4'