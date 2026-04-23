async def test_create_org_success(mock_app):
    """
    GIVEN: Valid organization creation request
    WHEN: POST /api/organizations is called
    THEN: Organization is created and returned with 201 status
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
        enable_proactive_conversation_starters=True,
    )

    request_data = {
        'name': 'Test Organization',
        'contact_name': 'John Doe',
        'contact_email': 'john@example.com',
    }

    with (
        patch(
            'server.routes.orgs.OrgService.create_org_with_owner',
            AsyncMock(return_value=mock_org),
        ),
        patch(
            'server.routes.orgs.OrgService.get_org_credits',
            AsyncMock(return_value=100.0),
        ),
    ):
        client = TestClient(mock_app)

        # Act
        response = client.post('/api/organizations', json=request_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data['name'] == 'Test Organization'
        assert response_data['contact_name'] == 'John Doe'
        assert response_data['contact_email'] == 'john@example.com'
        assert response_data['credits'] == 100.0
        assert response_data['org_version'] == 5
        assert (
            response_data['agent_settings']['llm']['model']
            == 'claude-opus-4-5-20251101'
        )