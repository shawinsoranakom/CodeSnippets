async def test_pipeline_save_audio(
    hass: HomeAssistant,
    mock_stt_provider: MockSTTProvider,
    mock_wake_word_provider_entity: MockWakeWordEntity,
    init_supporting_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test saving audio during a pipeline run."""
    with tempfile.TemporaryDirectory() as temp_dir_str:
        # Enable audio recording to temporary directory
        temp_dir = Path(temp_dir_str)
        assert await async_setup_component(
            hass,
            DOMAIN,
            {DOMAIN: {CONF_DEBUG_RECORDING_DIR: temp_dir_str}},
        )

        pipeline = assist_pipeline.async_get_pipeline(hass)
        events: list[assist_pipeline.PipelineEvent] = []

        async def audio_data():
            yield make_10ms_chunk(b"wake word")
            # queued audio
            yield make_10ms_chunk(b"part1")
            yield make_10ms_chunk(b"part2")
            yield b""

        await assist_pipeline.async_pipeline_from_audio_stream(
            hass,
            context=Context(),
            event_callback=events.append,
            stt_metadata=stt.SpeechMetadata(
                language="",
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            stt_stream=audio_data(),
            pipeline_id=pipeline.id,
            start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
            end_stage=assist_pipeline.PipelineStage.STT,
            audio_settings=assist_pipeline.AudioSettings(is_vad_enabled=False),
        )

        pipeline_dirs = list(temp_dir.iterdir())

        # Only one pipeline run
        # <debug_recording_dir>/<pipeline.name>/<run.id>
        assert len(pipeline_dirs) == 1
        assert pipeline_dirs[0].is_dir()
        assert pipeline_dirs[0].name == pipeline.name

        # Wake and stt files
        run_dirs = list(pipeline_dirs[0].iterdir())
        assert run_dirs[0].is_dir()
        run_files = list(run_dirs[0].iterdir())

        assert len(run_files) == 2
        wake_file = run_files[0] if "wake" in run_files[0].name else run_files[1]
        stt_file = run_files[0] if "stt" in run_files[0].name else run_files[1]
        assert wake_file != stt_file

        # Verify wake file
        with wave.open(str(wake_file), "rb") as wake_wav:
            wake_data = wake_wav.readframes(wake_wav.getnframes())
            assert wake_data.startswith(b"wake word")

        # Verify stt file
        with wave.open(str(stt_file), "rb") as stt_wav:
            stt_data = stt_wav.readframes(stt_wav.getnframes())
            assert stt_data.startswith(b"queued audio")
            stt_data = stt_data[len(b"queued audio") :]
            assert stt_data.startswith(b"part1")
            stt_data = stt_data[BYTES_PER_CHUNK:]
            assert stt_data.startswith(b"part2")