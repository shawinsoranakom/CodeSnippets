async def test_generate_data_preferred_entity(
    hass: HomeAssistant,
    init_components: None,
    mock_ai_task_entity: MockAITaskEntity,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test generating data with entity via preferences."""
    client = await hass_ws_client(hass)

    with pytest.raises(
        HomeAssistantError, match="No entity_id provided and no preferred entity set"
    ):
        await async_generate_data(
            hass,
            task_name="Test Task",
            instructions="Test prompt",
        )

    await client.send_json_auto_id(
        {
            "type": "ai_task/preferences/set",
            "gen_data_entity_id": "ai_task.unknown",
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    with pytest.raises(
        HomeAssistantError, match="AI Task entity ai_task.unknown not found"
    ):
        await async_generate_data(
            hass,
            task_name="Test Task",
            instructions="Test prompt",
        )

    await client.send_json_auto_id(
        {
            "type": "ai_task/preferences/set",
            "gen_data_entity_id": TEST_ENTITY_ID,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_UNKNOWN

    llm_api = llm.AssistAPI(hass)
    result = await async_generate_data(
        hass,
        task_name="Test Task",
        instructions="Test prompt",
        llm_api=llm_api,
    )
    assert result.data == "Mock result"
    as_dict = result.as_dict()
    assert as_dict["conversation_id"] == result.conversation_id
    assert as_dict["data"] == "Mock result"
    state = hass.states.get(TEST_ENTITY_ID)
    assert state is not None
    assert state.state != STATE_UNKNOWN

    with (
        chat_session.async_get_chat_session(hass, result.conversation_id) as session,
        async_get_chat_log(hass, session) as chat_log,
    ):
        assert chat_log.llm_api.api is llm_api

    mock_ai_task_entity.supported_features = AITaskEntityFeature(0)
    with pytest.raises(
        HomeAssistantError,
        match="AI Task entity ai_task.test_task_entity does not support generating data",
    ):
        await async_generate_data(
            hass,
            task_name="Test Task",
            instructions="Test prompt",
        )