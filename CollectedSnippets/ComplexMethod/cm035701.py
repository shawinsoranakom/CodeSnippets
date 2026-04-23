def test_settings_from_config():
    mock_app_config = OpenHandsConfig(
        default_agent='test-agent',
        max_iterations=100,
        security=SecurityConfig(
            security_analyzer='llm',
            confirmation_mode=True,
        ),
        llms={
            'llm': LLMConfig(
                model='test-model',
                api_key=SecretStr('test-key'),
                base_url='https://test.example.com',
            )
        },
        sandbox=SandboxConfig(remote_runtime_resource_factor=2),
    )

    with patch(
        'openhands.storage.data_models.settings.load_openhands_config',
        return_value=mock_app_config,
    ):
        settings = Settings.from_config()

        assert settings is not None
        assert settings.language == 'en'
        assert settings.agent_settings.agent == 'test-agent'
        assert settings.conversation_settings.max_iterations == 100
        assert settings.conversation_settings.security_analyzer == 'llm'
        assert settings.conversation_settings.confirmation_mode is True
        assert settings.agent_settings.llm.model == 'test-model'
        assert settings.agent_settings.llm.api_key.get_secret_value() == 'test-key'
        assert settings.agent_settings.llm.base_url == 'https://test.example.com'
        assert settings.remote_runtime_resource_factor == 2
        assert not settings.secrets_store.provider_tokens