async def test_pipeline_language_used_instead_of_conversation_language(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    mock_chat_session: chat_session.ChatSession,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that the pipeline language is used last when the conversation language is '*' (all languages)."""
    client = await hass_ws_client(hass)

    events: list[assist_pipeline.PipelineEvent] = []

    await client.send_json_auto_id(
        {
            "type": "assist_pipeline/pipeline/create",
            "conversation_engine": conversation.HOME_ASSISTANT_AGENT,
            "conversation_language": MATCH_ALL,
            "language": "en",
            "name": "test_name",
            "stt_engine": None,
            "stt_language": None,
            "tts_engine": None,
            "tts_language": None,
            "tts_voice": None,
            "wake_word_entity": None,
            "wake_word_id": None,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    pipeline_id = msg["result"]["id"]
    pipeline = assist_pipeline.async_get_pipeline(hass, pipeline_id)

    pipeline_input = assist_pipeline.pipeline.PipelineInput(
        intent_input="test input",
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
    await pipeline_input.validate()

    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_converse",
        return_value=conversation.ConversationResult(
            intent.IntentResponse(pipeline.language)
        ),
    ) as mock_async_converse:
        await pipeline_input.execute()

        # Check intent start event
        assert process_events(events) == snapshot
        intent_start: assist_pipeline.PipelineEvent | None = None
        for event in events:
            if event.type == assist_pipeline.PipelineEventType.INTENT_START:
                intent_start = event
                break

        assert intent_start is not None

        # STT language (en-US) should be used instead of '*'
        assert intent_start.data.get("language") == pipeline.language

        # Check input to async_converse
        mock_async_converse.assert_called_once()
        assert (
            mock_async_converse.call_args_list[0].kwargs.get("language")
            == pipeline.language
        )