async def test_get_tts_audio_streaming(
    hass: HomeAssistant, init_wyoming_streaming_tts, snapshot: SnapshotAssertion
) -> None:
    """Test get audio with streaming."""
    entity = hass.data[DATA_INSTANCES]["tts"].get_entity("tts.test_streaming_tts")
    assert entity is not None
    assert entity.async_supports_streaming_input()

    audio = bytes(100)

    # Verify audio
    audio_events = [
        AudioStart(rate=16000, width=2, channels=1).event(),
        AudioChunk(audio=audio, rate=16000, width=2, channels=1).event(),
        AudioStop().event(),
        SynthesizeStopped().event(),
    ]

    async def message_gen():
        yield "Hello "
        yield "Word."

    with patch(
        "homeassistant.components.wyoming.tts.AsyncTcpClient",
        MockAsyncTcpClient(audio_events),
    ) as mock_client:
        stream = tts.async_create_stream(
            hass,
            "tts.test_streaming_tts",
            "en-US",
            options={tts.ATTR_PREFERRED_FORMAT: "wav"},
        )
        stream.async_set_message_stream(message_gen())
        data = b"".join([chunk async for chunk in stream.async_stream_result()])

        # Ensure client was disconnected properly
        assert mock_client.is_connected is False

    assert data is not None
    with io.BytesIO(data) as wav_io, wave.open(wav_io, "rb") as wav_file:
        assert wav_file.getframerate() == 16000
        assert wav_file.getsampwidth() == 2
        assert wav_file.getnchannels() == 1
        assert wav_file.getnframes() == 0  # streaming
        assert data[44:] == audio  # WAV header is 44 bytes

    assert mock_client.written == snapshot