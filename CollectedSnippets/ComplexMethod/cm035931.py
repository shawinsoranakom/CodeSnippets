async def test_list_user_orgs_all_fields_present(mock_app_list):
    """
    GIVEN: Organization with all fields populated
    WHEN: GET /api/organizations is called
    THEN: All organization fields are included in response
    """
    # Arrange
    org_id = uuid.uuid4()
    mock_org = Org(
        id=org_id,
        name='Complete Org',
        contact_name='John Doe',
        contact_email='john@example.com',
        conversation_expiration=3600,
        agent_settings={
            'agent': 'CodeActAgent',
            'llm': {
                'model': 'claude-opus-4-5-20251101',
                'base_url': 'https://api.example.com',
            },
            'condenser': {'enabled': True},
        },
        conversation_settings={
            'max_iterations': 50,
            'security_analyzer': 'llm',
            'confirmation_mode': True,
        },
        remote_runtime_resource_factor=2,
        billing_margin=0.15,
        enable_proactive_conversation_starters=True,
        sandbox_base_container_image='test-image',
        sandbox_runtime_container_image='test-runtime',
        org_version=5,
        max_budget_per_task=1000.0,
        enable_solvability_analysis=True,
        v1_enabled=True,
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
        org_data = response_data['items'][0]
        assert org_data['name'] == 'Complete Org'
        assert org_data['contact_name'] == 'John Doe'
        assert org_data['contact_email'] == 'john@example.com'
        assert org_data['conversation_expiration'] == 3600
        assert org_data['agent_settings']['agent'] == 'CodeActAgent'
        assert org_data['agent_settings']['llm']['model'] == 'claude-opus-4-5-20251101'
        assert (
            org_data['agent_settings']['llm']['base_url'] == 'https://api.example.com'
        )
        assert org_data['conversation_settings']['max_iterations'] == 50
        assert org_data['conversation_settings']['security_analyzer'] == 'llm'
        assert org_data['conversation_settings']['confirmation_mode'] is True
        assert org_data['remote_runtime_resource_factor'] == 2
        assert org_data['billing_margin'] == 0.15
        assert org_data['enable_proactive_conversation_starters'] is True
        assert org_data['sandbox_base_container_image'] == 'test-image'
        assert org_data['sandbox_runtime_container_image'] == 'test-runtime'
        assert org_data['org_version'] == 5
        assert org_data['max_budget_per_task'] == 1000.0
        assert org_data['enable_solvability_analysis'] is True
        assert org_data['v1_enabled'] is True
        assert org_data['credits'] is None