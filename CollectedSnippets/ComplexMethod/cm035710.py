async def test_store_and_load_data(file_settings_store):
    # Test data
    init_data = Settings(
        language='python',
        agent_settings=AgentSettings(
            agent='test-agent',
            llm=LLM(
                model='test-model',
                api_key=SecretStr('test-key'),
                base_url='https://test.com',
            ),
        ),
        conversation_settings=ConversationSettings(
            max_iterations=100,
            security_analyzer='llm',
            confirmation_mode=True,
        ),
    )

    # Store data
    await file_settings_store.store(init_data)

    # Verify store called with correct JSON
    expected_json = init_data.model_dump_json(
        context={'expose_secrets': True, 'persist_settings': True}
    )
    file_settings_store.file_store.write.assert_called_once_with(
        'settings.json', expected_json
    )

    # Setup mock for load
    file_settings_store.file_store.read.return_value = expected_json

    # Load and verify data
    loaded_data = await file_settings_store.load()
    assert loaded_data is not None
    assert loaded_data.language == init_data.language
    assert loaded_data.agent_settings.agent == init_data.agent_settings.agent
    assert (
        loaded_data.conversation_settings.max_iterations
        == init_data.conversation_settings.max_iterations
    )
    assert (
        loaded_data.conversation_settings.security_analyzer
        == init_data.conversation_settings.security_analyzer
    )
    assert (
        loaded_data.conversation_settings.confirmation_mode
        == init_data.conversation_settings.confirmation_mode
    )
    assert loaded_data.agent_settings.llm.model == init_data.agent_settings.llm.model
    assert loaded_data.agent_settings.llm.api_key is not None
    assert init_data.agent_settings.llm.api_key is not None
    assert (
        loaded_data.agent_settings.llm.api_key.get_secret_value()
        == init_data.agent_settings.llm.api_key.get_secret_value()
    )
    assert (
        loaded_data.agent_settings.llm.base_url == init_data.agent_settings.llm.base_url
    )