async def test_store_and_load_keycloak_user(settings_store):
    # Set a UUID-like Keycloak user ID
    settings_store.user_id = '550e8400-e29b-41d4-a716-446655440000'
    settings = DataSettings(
        email='test@example.com',
        email_verified=True,
    )
    settings.update(
        {
            'agent_settings_diff': {
                'agent': 'smith',
                'llm': {
                    'model': 'anthropic/claude-sonnet-4-5-20250929',
                    'api_key': 'secret_key',
                    'base_url': LITE_LLM_API_URL,
                },
                'verification': {
                    'critic_mode': 'all_actions',
                    'critic_enabled': True,
                },
            },
        }
    )

    await settings_store.store(settings)

    # Load and verify settings
    loaded_settings = await settings_store.load()
    assert loaded_settings is not None
    assert _agent_value(loaded_settings, 'verification.critic_mode') == 'all_actions'
    assert _agent_value(loaded_settings, 'verification.critic_enabled') is True
    assert _secret_value(loaded_settings, 'llm.api_key') == 'secret_key'
    assert _agent_value(loaded_settings, 'agent') == 'smith'

    # Verify it was stored in user_settings table with keycloak_user_id
    from sqlalchemy import select

    async with settings_store.a_session_maker() as session:
        result = await session.execute(
            select(UserSettings).filter(
                UserSettings.keycloak_user_id == '550e8400-e29b-41d4-a716-446655440000'
            )
        )
        stored = result.scalars().first()
        assert stored is not None
        assert stored.agent_settings['agent'] == 'smith'