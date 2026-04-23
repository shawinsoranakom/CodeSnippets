async def test_get_tts_audio(
    hass: HomeAssistant, init_wyoming_tts, snapshot: SnapshotAssertion
) -> None:
    """Test get audio."""
    entity = hass.data[DATA_INSTANCES]["tts"].get_entity("tts.test_tts")
    assert entity is not None
    assert not entity.async_supports_streaming_input()

    audio = bytes(100)

    # Verify audio
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
                options={tts.ATTR_PREFERRED_FORMAT: "wav"},
            ),
        )

    assert extension == "wav"
    assert data is not None
    with io.BytesIO(data) as wav_io, wave.open(wav_io, "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getsampwidth() == 2
        assert wav_file.getnchannels() == 1

        # nframes = 0 due to streaming
        assert len(data) == len(audio) + 44  # WAVE header is 44 bytes
        assert data[44:] == audio

    assert mock_client.written == snapshot