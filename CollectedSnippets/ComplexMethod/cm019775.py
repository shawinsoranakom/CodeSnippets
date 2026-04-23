async def test_wake_word_start_keeps_responding(
    hass: HomeAssistant, init_components: ConfigEntry, entity: MockAssistSatellite
) -> None:
    """Test entity state stays responding on wake word start event."""

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == AssistSatelliteState.IDLE

    # Get into responding state
    audio_stream = object()

    with patch(
        "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream"
    ) as mock_start_pipeline:
        await entity.async_accept_pipeline_from_satellite(
            audio_stream, start_stage=PipelineStage.TTS
        )

    assert mock_start_pipeline.called
    kwargs = mock_start_pipeline.call_args[1]
    event_callback = kwargs["event_callback"]
    event_callback(PipelineEvent(PipelineEventType.TTS_START, {}))

    state = hass.states.get(ENTITY_ID)
    assert state.state == AssistSatelliteState.RESPONDING

    # Verify that starting a new wake word stream keeps the state
    audio_stream = object()

    with patch(
        "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream"
    ) as mock_start_pipeline:
        await entity.async_accept_pipeline_from_satellite(
            audio_stream, start_stage=PipelineStage.WAKE_WORD
        )

    assert mock_start_pipeline.called
    kwargs = mock_start_pipeline.call_args[1]
    event_callback = kwargs["event_callback"]
    event_callback(PipelineEvent(PipelineEventType.WAKE_WORD_START, {}))

    state = hass.states.get(ENTITY_ID)
    assert state.state == AssistSatelliteState.RESPONDING

    # Only return to idle once TTS is finished
    entity.tts_response_finished()
    state = hass.states.get(ENTITY_ID)
    assert state.state == AssistSatelliteState.IDLE