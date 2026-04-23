async def test_list_user_orgs_success(mock_app_list):
    """
    GIVEN: User has organizations
    WHEN: GET /api/organizations is called
    THEN: Paginated list of organizations is returned with 200 status
    """
    # Arrange
    org_id = uuid.uuid4()
    mock_org = Org(
        id=org_id,
        name='Test Organization',
        contact_name='John Doe',
        contact_email='john@example.com',
        org_version=5,
        agent_settings={
            'llm': {'model': 'claude-opus-4-5-20251101'},
        },
    )
    mock_user = MagicMock()
    mock_user.current_org_id = org_id

    with (
        patch(
            'server.routes.orgs.UserStore.get_user_by_id',
            AsyncMock(return_value=mock_user),
        ),
        patch(
            'server.routes.orgs.OrgService.get_user_orgs_paginated',
            AsyncMock(return_value=([mock_org], None)),
        ),
    ):
        client = TestClient(mock_app_list)

        # Act
        response = client.get('/api/organizations')

        # Assert
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert 'items' in response_data
        assert 'next_page_id' in response_data
        assert len(response_data['items']) == 1
        assert response_data['items'][0]['name'] == 'Test Organization'
        assert response_data['items'][0]['id'] == str(org_id)
        assert response_data['next_page_id'] is None
        # Credits should be None in list view
        assert response_data['items'][0]['credits'] is None