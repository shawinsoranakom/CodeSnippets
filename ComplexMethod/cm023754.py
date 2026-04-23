async def test_get_tts_audio_different_formats(
    hass: HomeAssistant, init_wyoming_tts, snapshot: SnapshotAssertion
) -> None:
    """Test changing preferred audio format."""
    audio = bytes(16000 * 2 * 1)  # one second
    audio_events = [
        AudioStart(rate=16000, width=2, channels=1).event(),
        AudioChunk(audio=audio, rate=16000, width=2, channels=1).event(),
        AudioStop().event(),
    ]

    # Request a different sample rate, etc.
    with patch(
        "homeassistant.components.wyoming.tts.AsyncTcpClient",
        MockAsyncTcpClient(audio_events),
    ) as mock_client:
        extension, data = await tts.async_get_media_source_audio(
            hass,
            tts.generate_media_source_id(
                hass,
                "Hello world",
                "tts.test_tts",
                "en-US",
                options={
                    tts.ATTR_PREFERRED_FORMAT: "wav",
                    tts.ATTR_PREFERRED_SAMPLE_RATE: 48000,
                    tts.ATTR_PREFERRED_SAMPLE_CHANNELS: 2,
                },
            ),
        )

    assert extension == "wav"
    assert data is not None
    with io.BytesIO(data) as wav_io, wave.open(wav_io, "rb") as wav_file:
        assert wav_file.getframerate() == 48000
        assert wav_file.getsampwidth() == 2
        assert wav_file.getnchannels() == 2

    assert mock_client.written == snapshot

    # MP3 is the default
    audio_events = [
        AudioStart(rate=16000, width=2, channels=1).event(),
        AudioChunk(audio=audio, rate=16000, width=2, channels=1).event(),
        AudioStop().event(),
    ]

    with patch(
        "homeassistant.components.wyoming.tts.AsyncTcpClient",
        MockAsyncTcpClient(audio_events),
    ) as mock_client:
        extension, data = await tts.async_get_media_source_audio(
            hass,
            tts.generate_media_source_id(
                hass,
                "Hello world",
                "tts.test_tts",
                "en-US",
            ),
        )

    assert extension == "mp3"
    assert b"ID3" in data
    assert mock_client.written == snapshot