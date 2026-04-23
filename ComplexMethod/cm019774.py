async def test_entity_state(
    hass: HomeAssistant, init_components: ConfigEntry, entity: MockAssistSatellite
) -> None:
    """Test entity state represent events."""

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == AssistSatelliteState.IDLE

    context = Context()
    audio_stream = object()

    entity.async_set_context(context)

    with patch(
        "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream"
    ) as mock_start_pipeline:
        await entity.async_accept_pipeline_from_satellite(audio_stream)

    assert mock_start_pipeline.called
    kwargs = mock_start_pipeline.call_args[1]
    assert kwargs["context"] is context
    assert kwargs["event_callback"] == entity._internal_on_pipeline_event
    assert kwargs["stt_metadata"] == stt.SpeechMetadata(
        language="",
        format=stt.AudioFormats.WAV,
        codec=stt.AudioCodecs.PCM,
        bit_rate=stt.AudioBitRates.BITRATE_16,
        sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
        channel=stt.AudioChannels.CHANNEL_MONO,
    )
    assert kwargs["stt_stream"] is audio_stream
    assert kwargs["pipeline_id"] is None
    assert kwargs["device_id"] is entity.device_entry.id
    assert kwargs["tts_audio_output"] == {"test-option": "test-value"}
    assert kwargs["wake_word_phrase"] is None
    assert kwargs["audio_settings"] == AudioSettings(
        silence_seconds=vad.VadSensitivity.to_seconds(vad.VadSensitivity.DEFAULT)
    )
    assert kwargs["start_stage"] == PipelineStage.STT
    assert kwargs["end_stage"] == PipelineStage.TTS

    for event_type, event_data, expected_state in (
        (PipelineEventType.RUN_START, {}, AssistSatelliteState.IDLE),
        (PipelineEventType.RUN_END, {}, AssistSatelliteState.IDLE),
        (
            PipelineEventType.WAKE_WORD_START,
            {},
            AssistSatelliteState.IDLE,
        ),
        (PipelineEventType.WAKE_WORD_END, {}, AssistSatelliteState.IDLE),
        (PipelineEventType.STT_START, {}, AssistSatelliteState.LISTENING),
        (PipelineEventType.STT_VAD_START, {}, AssistSatelliteState.LISTENING),
        (PipelineEventType.STT_VAD_END, {}, AssistSatelliteState.LISTENING),
        (PipelineEventType.STT_END, {}, AssistSatelliteState.LISTENING),
        (PipelineEventType.INTENT_START, {}, AssistSatelliteState.PROCESSING),
        (
            PipelineEventType.INTENT_END,
            {
                "intent_output": {
                    "conversation_id": "mock-conversation-id",
                }
            },
            AssistSatelliteState.PROCESSING,
        ),
        (PipelineEventType.TTS_START, {}, AssistSatelliteState.RESPONDING),
        (PipelineEventType.TTS_END, {}, AssistSatelliteState.RESPONDING),
        (PipelineEventType.ERROR, {}, AssistSatelliteState.RESPONDING),
    ):
        kwargs["event_callback"](PipelineEvent(event_type, event_data))
        state = hass.states.get(ENTITY_ID)
        assert state.state == expected_state, event_type

    entity.tts_response_finished()
    state = hass.states.get(ENTITY_ID)
    assert state.state == AssistSatelliteState.IDLE