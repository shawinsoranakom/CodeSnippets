async def test_create_org_with_owner_success(
    session_maker, async_session_maker, owner_role, mock_litellm_api
):
    """
    GIVEN: Valid organization data and user ID
    WHEN: create_org_with_owner is called
    THEN: Organization and owner membership are created successfully
    """
    # Arrange
    org_name = 'test-org'
    contact_name = 'John Doe'
    contact_email = 'john@example.com'
    user_id = uuid.uuid4()
    temp_org_id = uuid.uuid4()

    # Create user in database first
    with session_maker() as session:
        user = User(id=user_id, current_org_id=temp_org_id)
        session.add(user)
        session.commit()

    mock_settings = {'team_id': 'test-team', 'user_id': str(user_id)}

    with (
        patch('storage.org_store.a_session_maker', async_session_maker),
        patch('storage.role_store.a_session_maker', async_session_maker),
        patch(
            'storage.org_service.UserStore.create_default_settings',
            AsyncMock(return_value=mock_settings),
        ),
        patch(
            'storage.org_service.OrgStore.get_kwargs_from_settings',
            return_value={
                'agent_settings': {
                    'llm': {'model': 'anthropic/claude-sonnet-4-5-20250929'},
                },
                'conversation_settings': {},
            },
        ),
        patch(
            'storage.org_service.OrgMemberStore.get_kwargs_from_settings',
            return_value={'llm_api_key': 'test-key'},
        ),
    ):
        # Act
        result = await OrgService.create_org_with_owner(
            name=org_name,
            contact_name=contact_name,
            contact_email=contact_email,
            user_id=str(user_id),
        )

        # Assert
        assert result is not None
        assert result.name == org_name
        assert result.contact_name == contact_name
        assert result.contact_email == contact_email
        assert result.org_version > 0  # Should be set to ORG_SETTINGS_VERSION
        assert (
            result.agent_settings['llm']['model']
            == 'anthropic/claude-sonnet-4-5-20250929'
        )

        # Verify organization was persisted
        with session_maker() as session:
            persisted_org = session.get(Org, result.id)
            assert persisted_org is not None
            assert persisted_org.name == org_name

            # Verify owner membership was created
            org_member = (
                session.query(OrgMember)
                .filter_by(org_id=result.id, user_id=user_id)
                .first()
            )
            assert org_member is not None
            assert org_member.role_id == 1  # owner role id
            assert org_member.status == 'active'