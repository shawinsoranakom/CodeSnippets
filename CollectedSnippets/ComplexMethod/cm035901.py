def test_get_kwargs_from_user_settings_uses_agent_settings_as_source_of_truth():
    user_settings = UserSettings(
        llm_api_key='legacy-secret',
        agent_settings={
            'agent': 'CodeActAgent',
            'llm': {
                'model': 'anthropic/claude-sonnet-4-5-20250929',
                'base_url': 'https://api.example.com',
            },
            'condenser': {
                'enabled': False,
                'max_size': 128,
            },
        },
        conversation_settings={
            'confirmation_mode': True,
            'security_analyzer': 'llm',
            'max_iterations': 42,
        },
    )

    kwargs = OrgMemberStore.get_kwargs_from_user_settings(user_settings)

    assert kwargs['llm_api_key'] == 'legacy-secret'
    assert kwargs['agent_settings_diff']['agent'] == 'CodeActAgent'
    assert (
        kwargs['agent_settings_diff']['llm']['model']
        == 'anthropic/claude-sonnet-4-5-20250929'
    )
    assert kwargs['agent_settings_diff']['llm']['base_url'] == 'https://api.example.com'
    assert kwargs['agent_settings_diff']['condenser']['enabled'] is False
    assert kwargs['agent_settings_diff']['condenser']['max_size'] == 128
    assert kwargs['conversation_settings_diff']['confirmation_mode'] is True
    assert kwargs['conversation_settings_diff']['security_analyzer'] == 'llm'
    assert kwargs['conversation_settings_diff']['max_iterations'] == 42