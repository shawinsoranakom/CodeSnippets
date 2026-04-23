async def test_settings_api_endpoints(test_client):
    """Test that the settings API endpoints work with the new auth system."""
    settings = Settings(
        language='en',
        remote_runtime_resource_factor=2,
        agent_settings=AgentSettings(
            agent='test-agent',
            llm=LLM(
                model='test-model',
                api_key=SecretStr('test-key'),
                base_url='https://test.com',
                timeout=123,
                litellm_extra_body={'metadata': {'tier': 'pro'}},
            ),
            verification=VerificationSettings(
                critic_enabled=True,
                critic_mode='all_actions',
                enable_iterative_refinement=True,
                critic_threshold=0.7,
                max_refinement_iterations=4,
            ),
        ),
        conversation_settings=ConversationSettings(
            max_iterations=100,
            confirmation_mode=True,
            security_analyzer='llm',
        ),
    )

    # Make the POST request to store settings (V1 endpoint)
    response = test_client.post('/api/v1/settings', json=_dump_update(settings))

    # We're not checking the exact response, just that it doesn't error
    assert response.status_code == 200

    # Test the GET settings endpoint (V1 endpoint)
    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    response_data = response.json()
    assert 'agent_settings_schema' not in response_data
    vals = response_data['agent_settings']
    assert vals['llm']['model'] == 'test-model'
    assert vals['llm']['timeout'] == 123
    assert vals['llm']['litellm_extra_body'] == {'metadata': {'tier': 'pro'}}
    assert vals['verification']['critic_enabled'] is True
    assert vals['verification']['critic_mode'] == 'all_actions'
    assert vals['verification']['enable_iterative_refinement'] is True
    assert vals['verification']['critic_threshold'] == 0.7
    assert vals['verification']['max_refinement_iterations'] == 4
    cs = response_data['conversation_settings']
    assert cs['confirmation_mode'] is True
    assert cs['security_analyzer'] == 'llm'
    assert cs['max_iterations'] == 100
    # V1 API sets api_key to None for security and uses llm_api_key_set flag instead
    assert vals['llm']['api_key'] is None
    assert response_data['llm_api_key_set'] is True

    # Test updating with partial settings — legacy flat fields should preserve existing
    partial_settings = {
        'language': 'fr',
        'llm_model': None,
        'llm_api_key': None,
    }

    response = test_client.post('/api/v1/settings', json=partial_settings)
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    assert response.json()['agent_settings']['llm']['timeout'] == 123