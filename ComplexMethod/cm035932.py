async def test_get_org_success(mock_app_with_get_user_id, mock_owner_role):
    """GIVEN: Valid org_id and authenticated member
    WHEN: GET /api/organizations/{org_id} is called
    THEN: the deprecated detail route still returns the organization response
    """
    org_id = uuid.uuid4()
    mock_org = Org(
        id=org_id,
        name='Test Organization',
        contact_name='John Doe',
        contact_email='john@example.com',
        org_version=5,
        agent_settings={
            'llm': {'model': 'claude-opus-4-5-20251101'},
            'condenser': {'enabled': True},
        },
        enable_proactive_conversation_starters=True,
    )

    with (
        patch(
            'server.auth.authorization.get_user_org_role',
            AsyncMock(return_value=mock_owner_role),
        ),
        patch(
            'server.routes.orgs.OrgService.get_org_by_id',
            AsyncMock(return_value=mock_org),
        ),
        patch(
            'server.routes.orgs.OrgService.get_org_credits',
            AsyncMock(return_value=75.5),
        ),
    ):
        client = TestClient(mock_app_with_get_user_id)
        response = client.get(f'/api/organizations/{org_id}')

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data['id'] == str(org_id)
    assert response_data['name'] == 'Test Organization'
    assert response_data['contact_name'] == 'John Doe'
    assert response_data['contact_email'] == 'john@example.com'
    assert response_data['credits'] == 75.5
    assert response_data['org_version'] == 5