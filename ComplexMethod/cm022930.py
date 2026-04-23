async def test_chat_log_tts_streaming(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    init_components,
    mock_chat_session: chat_session.ChatSession,
    snapshot: SnapshotAssertion,
    mock_tts_entity: MockTTSEntity,
    pipeline_data: assist_pipeline.pipeline.PipelineData,
    to_stream_deltas: tuple[dict | list[str]],
    expected_chunks: int,
    chunk_text: str,
) -> None:
    """Test that chat log events are streamed to the TTS entity."""
    text_deltas = [
        delta
        for deltas in to_stream_deltas
        if isinstance(deltas, list)
        for delta in deltas
    ]

    events: list[assist_pipeline.PipelineEvent] = []

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
            end_stage=assist_pipeline.PipelineStage.TTS,
            event_callback=events.append,
        ),
    )

    received_tts = []

    async def async_stream_tts_audio(
        request: tts.TTSAudioRequest,
    ) -> tts.TTSAudioResponse:
        """Mock stream TTS audio."""

        async def gen_data():
            async for msg in request.message_gen:
                received_tts.append(msg)
                yield msg.encode()

        return tts.TTSAudioResponse(
            extension="mp3",
            data_gen=gen_data(),
        )

    async def async_get_tts_audio(
        message: str,
        language: str,
        options: dict[str, Any] | None = None,
    ) -> tts.TtsAudioType:
        """Mock get TTS audio."""
        return ("mp3", b"".join([chunk.encode() for chunk in text_deltas]))

    mock_tts_entity.async_get_tts_audio = async_get_tts_audio
    mock_tts_entity.async_stream_tts_audio = async_stream_tts_audio
    mock_tts_entity.async_supports_streaming_input = Mock(return_value=True)

    with patch(
        "homeassistant.components.assist_pipeline.pipeline.conversation.async_get_agent_info",
        return_value=conversation.AgentInfo(
            id="test-agent",
            name="Test Agent",
            supports_streaming=True,
        ),
    ):
        await pipeline_input.validate()

    async def mock_converse(
        hass: HomeAssistant,
        text: str,
        conversation_id: str | None,
        context: Context,
        language: str | None = None,
        agent_id: str | None = None,
        device_id: str | None = None,
        satellite_id: str | None = None,
        extra_system_prompt: str | None = None,
    ):
        """Mock converse."""
        conversation_input = conversation.ConversationInput(
            text=text,
            context=context,
            conversation_id=conversation_id,
            device_id=device_id,
            satellite_id=satellite_id,
            language=language,
            agent_id=agent_id,
            extra_system_prompt=extra_system_prompt,
        )

        async def stream_llm_response():
            for deltas in to_stream_deltas:
                if isinstance(deltas, dict):
                    yield deltas
                else:
                    yield {"role": "assistant"}
                    for chunk in deltas:
                        yield {"content": chunk}

        with (
            chat_session.async_get_chat_session(hass, conversation_id) as session,
            conversation.async_get_chat_log(
                hass,
                session,
                conversation_input,
            ) as chat_log,
        ):
            await chat_log.async_provide_llm_data(
                conversation_input.as_llm_context("test"),
                user_llm_hass_api="assist",
                user_llm_prompt=None,
                user_extra_system_prompt=conversation_input.extra_system_prompt,
            )
            async for _content in chat_log.async_add_delta_content_stream(
                agent_id, stream_llm_response()
            ):
                pass
            intent_response = intent.IntentResponse(language)
            intent_response.async_set_speech("".join(to_stream_deltas[-1]))
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=chat_log.conversation_id,
                continue_conversation=chat_log.continue_conversation,
            )

    mock_tool = AsyncMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "Test function"
    mock_tool.parameters = vol.Schema({})
    mock_tool.async_call.return_value = "Test response"

    with (
        patch(
            "homeassistant.helpers.llm.AssistAPI._async_get_tools",
            return_value=[mock_tool],
        ),
        patch(
            "homeassistant.components.assist_pipeline.pipeline.conversation.async_converse",
            mock_converse,
        ),
    ):
        await pipeline_input.execute()

    stream = tts.async_get_stream(hass, events[0].data["tts_output"]["token"])
    assert stream is not None
    tts_result = "".join(
        [chunk.decode() async for chunk in stream.async_stream_result()]
    )

    streamed_text = "".join(text_deltas)
    assert tts_result == streamed_text
    assert len(received_tts) == expected_chunks
    assert "".join(received_tts) == chunk_text

    assert process_events(events) == snapshot