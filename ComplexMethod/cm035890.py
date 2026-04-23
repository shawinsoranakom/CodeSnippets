def test_member_settings_persist_full_effective_agent_settings(mock_config):
    settings = Settings()
    settings.update(
        {
            'agent_settings_diff': {
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
            'conversation_settings_diff': {
                'max_iterations': 42,
                'confirmation_mode': True,
                'security_analyzer': 'llm',
            },
        }
    )

    agent = settings.agent_settings
    assert agent.agent == 'CodeActAgent'
    assert agent.llm.model == 'anthropic/claude-sonnet-4-5-20250929'
    assert agent.llm.base_url == 'https://api.example.com'
    assert agent.condenser.enabled is False
    assert agent.condenser.max_size == 128

    # Conversation settings live on the Settings object, not in agent_settings
    assert settings.conversation_settings.max_iterations == 42
    assert settings.conversation_settings.confirmation_mode is True
    assert settings.conversation_settings.security_analyzer == 'llm'