async def test_list_user_orgs_mixed_personal_and_team(mock_app_list):
    """
    GIVEN: User has both personal and team organizations
    WHEN: GET /api/organizations is called
    THEN: is_personal field correctly identifies each org type
    """
    # Arrange
    user_id = mock_app_list.state.test_user_id
    personal_org_id = uuid.UUID(user_id)

    personal_org = Org(
        id=personal_org_id,
        name=f'user_{user_id}_org',
        contact_name='John Doe',
        contact_email='john@example.com',
    )

    team_org = Org(
        id=uuid.uuid4(),
        name='Team Organization',
        contact_name='Jane Doe',
        contact_email='jane@example.com',
    )
    mock_user = MagicMock()
    mock_user.current_org_id = personal_org_id

    with (
        patch(
            'server.routes.orgs.UserStore.get_user_by_id',
            AsyncMock(return_value=mock_user),
        ),
        patch(
            'server.routes.orgs.OrgService.get_user_orgs_paginated',
            AsyncMock(return_value=([personal_org, team_org], None)),
        ),
    ):
        client = TestClient(mock_app_list)

        # Act
        response = client.get('/api/organizations')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data['items']) == 2

        # Find personal and team orgs in response
        personal_org_response = next(
            item
            for item in response_data['items']
            if item['id'] == str(personal_org_id)
        )
        team_org_response = next(
            item
            for item in response_data['items']
            if item['id'] != str(personal_org_id)
        )

        assert personal_org_response['is_personal'] is True
        assert team_org_response['is_personal'] is False