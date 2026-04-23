async def test_tts_dict_preferred_format(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_tts_entity: MockTTSEntity,
    init_components,
    mock_chat_session: chat_session.ChatSession,
    pipeline_data: assist_pipeline.pipeline.PipelineData,
) -> None:
    """Test that preferred format options are given to the TTS system if supported."""
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
            tts_audio_output={
                tts.ATTR_PREFERRED_FORMAT: "flac",
                tts.ATTR_PREFERRED_SAMPLE_RATE: 48000,
                tts.ATTR_PREFERRED_SAMPLE_CHANNELS: 2,
                tts.ATTR_PREFERRED_SAMPLE_BYTES: 2,
            },
        ),
    )
    await pipeline_input.validate()

    # Make the TTS provider support preferred format options
    supported_options = list(mock_tts_entity.supported_options or [])
    supported_options.extend(
        [
            tts.ATTR_PREFERRED_FORMAT,
            tts.ATTR_PREFERRED_SAMPLE_RATE,
            tts.ATTR_PREFERRED_SAMPLE_CHANNELS,
            tts.ATTR_PREFERRED_SAMPLE_BYTES,
        ]
    )

    with (
        patch.object(mock_tts_entity, "_supported_options", supported_options),
        patch.object(mock_tts_entity, "get_tts_audio") as mock_get_tts_audio,
    ):
        await pipeline_input.execute()

        for event in events:
            if event.type == assist_pipeline.PipelineEventType.TTS_END:
                # We must fetch the media URL to trigger the TTS
                assert event.data
                await client.get(event.data["tts_output"]["url"])

        assert mock_get_tts_audio.called
        options = mock_get_tts_audio.call_args_list[0].kwargs["options"]

        # We should have received preferred format options in get_tts_audio
        assert options.get(tts.ATTR_PREFERRED_FORMAT) == "flac"
        assert int(options.get(tts.ATTR_PREFERRED_SAMPLE_RATE)) == 48000
        assert int(options.get(tts.ATTR_PREFERRED_SAMPLE_CHANNELS)) == 2
        assert int(options.get(tts.ATTR_PREFERRED_SAMPLE_BYTES)) == 2