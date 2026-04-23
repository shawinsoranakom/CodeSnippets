async def test_satellite_tts_streaming(hass: HomeAssistant) -> None:
    """Test running a streaming TTS pipeline with a satellite."""
    assert await async_setup_component(hass, assist_pipeline.DOMAIN, {})

    events = [
        RunPipeline(start_stage=PipelineStage.ASR, end_stage=PipelineStage.TTS).event(),
    ]

    pipeline_kwargs: dict[str, Any] = {}
    pipeline_event_callback: Callable[[assist_pipeline.PipelineEvent], None] | None = (
        None
    )
    run_pipeline_called = asyncio.Event()
    audio_chunk_received = asyncio.Event()

    async def async_pipeline_from_audio_stream(
        hass: HomeAssistant,
        context,
        event_callback,
        stt_metadata,
        stt_stream,
        **kwargs,
    ) -> None:
        nonlocal pipeline_kwargs, pipeline_event_callback
        pipeline_kwargs = kwargs
        pipeline_event_callback = event_callback

        run_pipeline_called.set()
        async for chunk in stt_stream:
            if chunk:
                audio_chunk_received.set()
                break

    with (
        patch(
            "homeassistant.components.wyoming.data.load_wyoming_info",
            return_value=SATELLITE_INFO,
        ),
        patch(
            "homeassistant.components.wyoming.assist_satellite.AsyncTcpClient",
            SatelliteAsyncTcpClient(events),
        ) as mock_client,
        patch(
            "homeassistant.components.assist_satellite.entity.async_pipeline_from_audio_stream",
            async_pipeline_from_audio_stream,
        ),
        patch("homeassistant.components.wyoming.assist_satellite._PING_SEND_DELAY", 0),
    ):
        entry = await setup_config_entry(hass)
        device: SatelliteDevice = entry.runtime_data.device
        assert device is not None

        async with asyncio.timeout(1):
            await mock_client.connect_event.wait()
            await mock_client.run_satellite_event.wait()

        async with asyncio.timeout(1):
            await run_pipeline_called.wait()

        assert pipeline_event_callback is not None
        assert pipeline_kwargs.get("device_id") == device.device_id

        # Send TTS info early
        mock_tts_result_stream = MockResultStream(hass, "wav", get_test_wav(1000))
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.RUN_START,
                {"tts_output": {"token": mock_tts_result_stream.token}},
            )
        )

        # Speech-to-text started
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_START,
                {"metadata": {"language": "en"}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.transcribe_event.wait()

        # Push in some audio
        mock_client.inject_event(
            AudioChunk(rate=16000, width=2, channels=1, audio=bytes(1024)).event()
        )

        # User started speaking
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_VAD_START, {"timestamp": 1234}
            )
        )
        async with asyncio.timeout(1):
            await mock_client.voice_started_event.wait()

        # User stopped speaking
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_VAD_END, {"timestamp": 5678}
            )
        )
        async with asyncio.timeout(1):
            await mock_client.voice_stopped_event.wait()

        # Speech-to-text transcription
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_END,
                {"stt_output": {"text": "test transcript"}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.transcript_event.wait()

        # Intent progress starts TTS streaming early with info received in the
        # run-start event.
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.INTENT_PROGRESS,
                {"tts_start_streaming": True},
            )
        )

        # TTS events are sent now. In practice, these would be streamed as text
        # chunks are generated.
        async with asyncio.timeout(1):
            await mock_client.tts_audio_start_event.wait()
            await mock_client.tts_audio_chunk_event.wait()
            await mock_client.tts_audio_stop_event.wait()

        # Verify audio chunks from test WAV
        assert len(mock_client.tts_audio_chunks) == 2
        chunk_sizes = (2048, 1952)  # 1024 samples per chunk
        for i, audio_chunk in enumerate(mock_client.tts_audio_chunks):
            assert audio_chunk.rate == 22050
            assert audio_chunk.width == 2
            assert audio_chunk.channels == 1
            assert len(audio_chunk.audio) == chunk_sizes[i]

        # Text-to-speech text
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.TTS_START,
                {
                    "tts_input": "test text to speak",
                    "voice": "test voice",
                },
            )
        )

        # synthesize event is sent with complete message for non-streaming clients
        async with asyncio.timeout(1):
            await mock_client.synthesize_event.wait()

        assert mock_client.synthesize is not None
        assert mock_client.synthesize.text == "test text to speak"
        assert mock_client.synthesize.voice is not None
        assert mock_client.synthesize.voice.name == "test voice"

        # Because we started streaming TTS after intent progress, we should not
        # stream it again on tts-end.
        with patch(
            "homeassistant.components.wyoming.assist_satellite.WyomingAssistSatellite._stream_tts"
        ) as mock_stream_tts:
            pipeline_event_callback(
                assist_pipeline.PipelineEvent(
                    assist_pipeline.PipelineEventType.TTS_END,
                    {"tts_output": {"token": mock_tts_result_stream.token}},
                )
            )

            mock_stream_tts.assert_not_called()

        # Pipeline finished
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(assist_pipeline.PipelineEventType.RUN_END)
        )

        # Stop the satellite
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()