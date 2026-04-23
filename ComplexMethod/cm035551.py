def test_get_conversation_settings_schema_endpoint(test_client):
    response = test_client.get('/api/v1/settings/conversation-schema')

    assert response.status_code == 200
    schema = response.json()
    assert schema['model_name'] == 'ConversationSettings'
    section_keys = [s['key'] for s in schema['sections']]
    assert section_keys == ['general', 'verification']
    verification_section = next(
        s for s in schema['sections'] if s['key'] == 'verification'
    )
    field_keys = [f['key'] for f in verification_section['fields']]
    assert 'confirmation_mode' in field_keys
    assert 'security_analyzer' in field_keys