def test_get_kwargs_from_settings():
    # Test extracting org kwargs from settings
    settings = Settings()
    settings.update(
        {
            'language': 'es',
            'enable_sound_notifications': True,
            'agent_settings_diff': {
                'agent': 'CodeActAgent',
                'llm': {
                    'model': 'anthropic/claude-sonnet-4-5-20250929',
                    'api_key': 'test-key',
                },
            },
        }
    )

    kwargs = OrgStore.get_kwargs_from_settings(settings)

    # Should only include fields that exist in Org model
    assert 'agent_settings' in kwargs
    assert 'agent' not in kwargs
    assert 'default_llm_model' not in kwargs
    assert kwargs['agent_settings']['agent'] == 'CodeActAgent'
    assert (
        kwargs['agent_settings']['llm']['model']
        == 'anthropic/claude-sonnet-4-5-20250929'
    )
    # Should not include fields that don't exist in Org model
    assert 'language' not in kwargs  # language is not in Org model
    assert 'llm_api_key' not in kwargs
    assert 'llm_model' not in kwargs
    assert 'enable_sound_notifications' not in kwargs