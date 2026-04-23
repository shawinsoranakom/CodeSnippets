async def test_disabled_skills_persistence(test_client):
    """Test that disabled_skills can be saved and retrieved via the settings API."""
    response = test_client.post(
        '/api/v1/settings',
        json=_dump_update(
            Settings(
                disabled_skills=['skill_a', 'skill_b'],
                agent_settings=AgentSettings(llm=LLM(model='test-model')),
            )
        ),
    )
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    data = response.json()
    assert data['disabled_skills'] == ['skill_a', 'skill_b']

    response = test_client.post(
        '/api/v1/settings',
        json=_dump(Settings(disabled_skills=['skill_c'])),
    )
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    data = response.json()
    assert data['disabled_skills'] == ['skill_c']

    response = test_client.post(
        '/api/v1/settings',
        json=_dump(Settings(disabled_skills=[])),
    )
    assert response.status_code == 200

    response = test_client.get('/api/v1/settings')
    assert response.status_code == 200
    data = response.json()
    assert data['disabled_skills'] == []