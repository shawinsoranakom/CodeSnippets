async def test_pipeline_from_audio_stream_wake_word(
    hass: HomeAssistant,
    mock_stt_provider_entity: MockSTTProviderEntity,
    mock_wake_word_provider_entity: MockWakeWordEntity,
    init_components,
    snapshot: SnapshotAssertion,
) -> None:
    """Test creating a pipeline from an audio stream with wake word."""

    events: list[assist_pipeline.PipelineEvent] = []

    # [0, 1, ...]
    wake_chunk_1 = bytes(it.islice(it.cycle(range(256)), BYTES_ONE_SECOND))

    # [0, 2, ...]
    wake_chunk_2 = bytes(it.islice(it.cycle(range(0, 256, 2)), BYTES_ONE_SECOND))

    samples_per_chunk = 160  # 10ms @ 16Khz
    bytes_per_chunk = samples_per_chunk * 2  # 16-bit

    async def audio_data():
        # 1 second in chunks
        i = 0
        while i < len(wake_chunk_1):
            yield wake_chunk_1[i : i + bytes_per_chunk]
            i += bytes_per_chunk

        # 1 second in chunks
        i = 0
        while i < len(wake_chunk_2):
            yield wake_chunk_2[i : i + bytes_per_chunk]
            i += bytes_per_chunk

        for header in (b"wake word!", b"part1", b"part2"):
            yield make_10ms_chunk(header)

        yield b""

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
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
            start_stage=assist_pipeline.PipelineStage.WAKE_WORD,
            wake_word_settings=assist_pipeline.WakeWordSettings(
                audio_seconds_to_buffer=1.5
            ),
            audio_settings=assist_pipeline.AudioSettings(is_vad_enabled=False),
        )

    assert process_events(events) == snapshot

    # 1. Half of wake_chunk_1 + all wake_chunk_2
    # 2. queued audio (from mock wake word entity)
    # 3. part1
    # 4. part2
    assert len(mock_stt_provider_entity.received) > 3

    first_chunk = bytes(
        [c_byte for c in mock_stt_provider_entity.received[:-3] for c_byte in c]
    )
    assert first_chunk == wake_chunk_1[len(wake_chunk_1) // 2 :] + wake_chunk_2

    assert mock_stt_provider_entity.received[-3] == b"queued audio"
    assert mock_stt_provider_entity.received[-2].startswith(b"part1")
    assert mock_stt_provider_entity.received[-1].startswith(b"part2")