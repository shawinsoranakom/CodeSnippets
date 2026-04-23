def test_get_agent_settings_schema_includes_critic_verification_fields(test_client):
    response = test_client.get('/api/v1/settings/agent-schema')

    assert response.status_code == 200
    schema = response.json()
    section_keys = [s['key'] for s in schema['sections']]
    assert 'verification' in section_keys
    section = next(s for s in schema['sections'] if s['key'] == 'verification')
    field_keys = [f['key'] for f in section['fields']]
    assert 'verification.critic_enabled' in field_keys
    assert 'confirmation_mode' not in field_keys
    assert 'security_analyzer' not in field_keys