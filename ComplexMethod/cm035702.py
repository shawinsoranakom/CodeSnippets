def test_settings_preserve_agent_settings():
    settings = Settings(
        agent_settings=AgentSettings(
            llm=LLM(
                model='test-model',
                api_key=SecretStr('test-key'),
                litellm_extra_body={'metadata': {'tier': 'pro'}},
            ),
            verification=VerificationSettings(
                critic_enabled=True,
                critic_mode='all_actions',
            ),
        ),
    )

    assert settings.agent_settings.llm.api_key.get_secret_value() == 'test-key'
    dump = settings.agent_settings.model_dump(
        mode='json', context={'expose_secrets': True}
    )

    assert dump['schema_version'] == AGENT_SETTINGS_SCHEMA_VERSION
    assert dump['llm']['model'] == 'test-model'
    assert dump['llm']['api_key'] == 'test-key'
    assert dump['verification']['critic_enabled'] is True
    assert dump['verification']['critic_mode'] == 'all_actions'
    assert dump['llm']['litellm_extra_body'] == {'metadata': {'tier': 'pro'}}