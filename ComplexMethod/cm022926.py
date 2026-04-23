async def test_intent_continue_conversation(
    hass: HomeAssistant,
    init_components,
    mock_chat_session: chat_session.ChatSession,
    pipeline_data: assist_pipeline.pipeline.PipelineData,
) -> None:
    """Test that a conversation agent flagging continue conversation gets response."""
    events: list[assist_pipeline.PipelineEvent] = []

    # Fake a test agent and prefer local intents
    pipeline_store = pipeline_data.pipeline_store
    pipeline_id = pipeline_store.async_get_preferred_item()
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass, pipeline_id)
    await assist_pipeline.pipeline.async_update_pipeline(
        hass, pipeline, conversation_engine="test-agent"
    )
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass, pipeline_id)

    pipeline_input = assist_pipeline.pipeline.PipelineInput(
        intent_input="Set a timer",
        session=mock_chat_session,
        run=assist_pipeline.pipeline.PipelineRun(
            hass,
            context=Context(),
            pipeline=pipeline,
            start_stage=assist_pipeline.PipelineStage.INTENT,
            end_stage=assist_pipeline.PipelineStage.INTENT,
            event_callback=events.append,
        ),
    )

    # Ensure prepare succeeds
    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_get_agent_info",
        return_value=conversation.AgentInfo(
            id="test-agent",
            name="Test Agent",
            supports_streaming=False,
        ),
    ):
        await pipeline_input.validate()

    response = intent.IntentResponse("en")
    response.async_set_speech("For how long?")

    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_converse",
        return_value=conversation.ConversationResult(
            response=response,
            conversation_id=mock_chat_session.conversation_id,
            continue_conversation=True,
        ),
    ) as mock_async_converse:
        await pipeline_input.execute()

        mock_async_converse.assert_called()

    results = [
        event.data
        for event in events
        if event.type
        in (
            assist_pipeline.PipelineEventType.INTENT_START,
            assist_pipeline.PipelineEventType.INTENT_END,
        )
    ]
    assert results[1]["intent_output"]["continue_conversation"] is True

    # Change conversation agent to default one and register sentence trigger that should not be called
    await assist_pipeline.pipeline.async_update_pipeline(
        hass, pipeline, conversation_engine=None
    )
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass, pipeline_id)
    assert await async_setup_component(
        hass,
        "automation",
        {
            "automation": {
                "trigger": {
                    "platform": "conversation",
                    "command": ["Hello"],
                },
                "action": {
                    "set_conversation_response": "test trigger response",
                },
            }
        },
    )

    # Because we did continue conversation, it should respond to the test agent again.
    events.clear()

    pipeline_input = assist_pipeline.pipeline.PipelineInput(
        intent_input="Hello",
        session=mock_chat_session,
        run=assist_pipeline.pipeline.PipelineRun(
            hass,
            context=Context(),
            pipeline=pipeline,
            start_stage=assist_pipeline.PipelineStage.INTENT,
            end_stage=assist_pipeline.PipelineStage.INTENT,
            event_callback=events.append,
        ),
    )

    # Ensure prepare succeeds
    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_get_agent_info",
        return_value=conversation.AgentInfo(
            id="test-agent",
            name="Test Agent",
            supports_streaming=False,
        ),
    ) as mock_prepare:
        await pipeline_input.validate()

    # It requested test agent even if that was not default agent.
    assert mock_prepare.mock_calls[0][1][1] == "test-agent"

    response = intent.IntentResponse("en")
    response.async_set_speech("Timer set for 20 minutes")

    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_converse",
        return_value=conversation.ConversationResult(
            response=response,
            conversation_id=mock_chat_session.conversation_id,
        ),
    ) as mock_async_converse:
        await pipeline_input.execute()

        mock_async_converse.assert_called()

    # Snapshot will show it was still handled by the test agent and not default agent
    results = [
        event.data
        for event in events
        if event.type
        in (
            assist_pipeline.PipelineEventType.INTENT_START,
            assist_pipeline.PipelineEventType.INTENT_END,
        )
    ]
    assert results[0]["engine"] == "test-agent"
    assert results[1]["intent_output"]["continue_conversation"] is False