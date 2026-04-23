async def test_satellite_pipeline(hass: HomeAssistant) -> None:
    """Test running a pipeline with a satellite."""
    assert await async_setup_component(hass, assist_pipeline.DOMAIN, {})

    events = [
        RunPipeline(
            start_stage=PipelineStage.WAKE,
            end_stage=PipelineStage.TTS,
            restart_on_end=True,
        ).event(),
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

            # Reset so we can check the pipeline is automatically restarted below
            run_pipeline_called.clear()

        assert pipeline_event_callback is not None
        assert pipeline_kwargs.get("device_id") == device.device_id

        # Test a ping
        mock_client.inject_event(Ping("test-ping").event())

        # Pong is expected with the same text
        async with asyncio.timeout(1):
            await mock_client.pong_event.wait()

        assert mock_client.pong is not None
        assert mock_client.pong.text == "test-ping"

        # The client should have received the first ping
        async with asyncio.timeout(1):
            await mock_client.ping_event.wait()

        assert mock_client.ping is not None

        # Reset and send a pong back.
        # We will get a second ping by the end of the test.
        mock_client.ping_event.clear()
        mock_client.ping = None
        mock_client.inject_event(Pong().event())

        # Start detecting wake word
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.WAKE_WORD_START
            )
        )
        async with asyncio.timeout(1):
            await mock_client.detect_event.wait()

        assert not device.is_active
        assert not device.is_muted

        # Push in some audio
        mock_client.inject_event(
            AudioChunk(rate=16000, width=2, channels=1, audio=bytes(1024)).event()
        )

        # Wake word is detected
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.WAKE_WORD_END,
                {"wake_word_output": {"wake_word_id": "test_wake_word"}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.detection_event.wait()

        assert mock_client.detection is not None
        assert mock_client.detection.name == "test_wake_word"

        # Speech-to-text started
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_START,
                {"metadata": {"language": "en"}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.transcribe_event.wait()

        assert mock_client.transcribe is not None
        assert mock_client.transcribe.language == "en"

        # "Assist in progress" sensor should be active now
        assert device.is_active

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

        assert mock_client.voice_started is not None
        assert mock_client.voice_started.timestamp == 1234

        # User stopped speaking
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_VAD_END, {"timestamp": 5678}
            )
        )
        async with asyncio.timeout(1):
            await mock_client.voice_stopped_event.wait()

        assert mock_client.voice_stopped is not None
        assert mock_client.voice_stopped.timestamp == 5678

        # Speech-to-text transcription
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.STT_END,
                {"stt_output": {"text": "test transcript"}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.transcript_event.wait()

        assert mock_client.transcript is not None
        assert mock_client.transcript.text == "test transcript"

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
        async with asyncio.timeout(1):
            await mock_client.synthesize_event.wait()

        assert mock_client.synthesize is not None
        assert mock_client.synthesize.text == "test text to speak"
        assert mock_client.synthesize.voice is not None
        assert mock_client.synthesize.voice.name == "test voice"

        # Text-to-speech media
        mock_tts_result_stream = MockResultStream(hass, "wav", get_test_wav())
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(
                assist_pipeline.PipelineEventType.TTS_END,
                {"tts_output": {"token": mock_tts_result_stream.token}},
            )
        )
        async with asyncio.timeout(1):
            await mock_client.tts_audio_start_event.wait()
            await mock_client.tts_audio_chunk_event.wait()
            await mock_client.tts_audio_stop_event.wait()

        # Verify audio chunk from test WAV
        assert mock_client.tts_audio_chunk is not None
        assert mock_client.tts_audio_chunk.rate == 22050
        assert mock_client.tts_audio_chunk.width == 2
        assert mock_client.tts_audio_chunk.channels == 1
        assert mock_client.tts_audio_chunk.audio == b"1234"

        # Pipeline finished
        pipeline_event_callback(
            assist_pipeline.PipelineEvent(assist_pipeline.PipelineEventType.RUN_END)
        )
        assert not device.is_active

        # Pipeline should automatically restart
        async with asyncio.timeout(1):
            await run_pipeline_called.wait()

        # Stop the satellite
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()