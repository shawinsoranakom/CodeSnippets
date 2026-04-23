async def test_tts_audio_output(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_tts_entity: MockTTSProvider,
    init_components,
    pipeline_data: assist_pipeline.pipeline.PipelineData,
    mock_chat_session: chat_session.ChatSession,
    snapshot: SnapshotAssertion,
) -> None:
    """Test using tts_audio_output with wav sets options correctly."""
    client = await hass_client()
    assert await async_setup_component(hass, media_source.DOMAIN, {})

    events: list[assist_pipeline.PipelineEvent] = []

    pipeline_store = pipeline_data.pipeline_store
    pipeline_id = pipeline_store.async_get_preferred_item()
    pipeline = assist_pipeline.pipeline.async_get_pipeline(hass, pipeline_id)

    pipeline_input = assist_pipeline.pipeline.PipelineInput(
        tts_input="This is a test.",
        session=mock_chat_session,
        device_id=None,
        run=assist_pipeline.pipeline.PipelineRun(
            hass,
            context=Context(),
            pipeline=pipeline,
            start_stage=assist_pipeline.PipelineStage.TTS,
            end_stage=assist_pipeline.PipelineStage.TTS,
            event_callback=events.append,
            tts_audio_output="wav",
        ),
    )
    await pipeline_input.validate()

    # Verify TTS audio settings
    assert pipeline_input.run.tts_stream.options is not None
    assert pipeline_input.run.tts_stream.options.get(tts.ATTR_PREFERRED_FORMAT) == "wav"
    assert (
        pipeline_input.run.tts_stream.options.get(tts.ATTR_PREFERRED_SAMPLE_RATE)
        == 16000
    )
    assert (
        pipeline_input.run.tts_stream.options.get(tts.ATTR_PREFERRED_SAMPLE_CHANNELS)
        == 1
    )

    with patch.object(mock_tts_entity, "get_tts_audio") as mock_get_tts_audio:
        await pipeline_input.execute()

        for event in events:
            if event.type == assist_pipeline.PipelineEventType.TTS_END:
                # We must fetch the media URL to trigger the TTS
                assert event.data
                await client.get(event.data["tts_output"]["url"])

        # Ensure that no unsupported options were passed in
        assert mock_get_tts_audio.called
        options = mock_get_tts_audio.call_args_list[0].kwargs["options"]
        extra_options = set(options).difference(mock_tts_entity.supported_options)
        assert len(extra_options) == 0, extra_options