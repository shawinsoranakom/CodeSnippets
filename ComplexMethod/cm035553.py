async def test_search_api_key_explicit_clear(test_client):
    """Explicit empty search_api_key payloads should clear the stored secret."""
    response = test_client.post(
        '/api/v1/settings',
        json=_dump_update(
            Settings(
                search_api_key='initial-secret-key',
                agent_settings=AgentSettings(llm=LLM(model='gpt-4')),
            )
        ),
    )
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    assert response.json()['search_api_key_set'] is True

    response = test_client.post(
        '/api/v1/settings',
        json=_dump_update(
            Settings(
                search_api_key='',
                agent_settings=AgentSettings(llm=LLM(model='claude-3-opus')),
            )
        ),
    )
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    assert response.json()['search_api_key_set'] is False
    assert response.json()['agent_settings']['llm']['model'] == 'claude-3-opus'