def test_settings_to_agent_settings_uses_agent_vals():
    settings = Settings(
        agent_settings=AgentSettings(
            llm=LLM(
                model='sdk-model',
                base_url='https://sdk.example.com',
                litellm_extra_body={'metadata': {'tier': 'enterprise'}},
            ),
            condenser=CondenserSettings(enabled=False, max_size=88),
            verification=VerificationSettings(
                critic_enabled=True, critic_mode='all_actions'
            ),
        ),
    )

    agent_settings = settings.to_agent_settings()

    assert agent_settings.llm.model == 'sdk-model'
    assert agent_settings.llm.base_url == 'https://sdk.example.com'
    assert agent_settings.llm.litellm_extra_body == {'metadata': {'tier': 'enterprise'}}
    assert agent_settings.condenser.enabled is False
    assert agent_settings.condenser.max_size == 88
    assert agent_settings.verification.critic_enabled is True
    assert agent_settings.verification.critic_mode == 'all_actions'