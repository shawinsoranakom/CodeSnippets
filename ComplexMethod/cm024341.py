async def test_stream(hass: HomeAssistant, mock_tts_entity: MockTTSEntity) -> None:
    """Test creating streams."""
    await mock_config_entry_setup(hass, mock_tts_entity)

    stream = tts.async_create_stream(hass, mock_tts_entity.entity_id)
    assert stream.language == mock_tts_entity.default_language
    assert stream.options == (mock_tts_entity.default_options or {})
    assert stream.supports_streaming_input is False
    assert tts.async_get_stream(hass, stream.token) is stream
    stream.async_set_message("beer")
    result_data = b"".join([chunk async for chunk in stream.async_stream_result()])
    assert result_data == MOCK_DATA

    async def async_stream_tts_audio(
        request: tts.TTSAudioRequest,
    ) -> tts.TTSAudioResponse:
        """Mock stream TTS audio."""

        async def gen_data():
            async for msg in request.message_gen:
                yield msg.encode()

        return tts.TTSAudioResponse(
            extension="mp3",
            data_gen=gen_data(),
        )

    mock_tts_entity.async_stream_tts_audio = async_stream_tts_audio
    mock_tts_entity.async_supports_streaming_input = Mock(return_value=True)

    async def stream_message():
        """Mock stream message."""
        yield "he"
        yield "ll"
        yield "o"

    stream = tts.async_create_stream(hass, mock_tts_entity.entity_id)
    assert stream.supports_streaming_input is True
    stream.async_set_message_stream(stream_message())
    result_data = b"".join([chunk async for chunk in stream.async_stream_result()])
    assert result_data == b"hello"

    data = b"beer"
    stream2 = MockResultStream(hass, "wav", data)
    assert tts.async_get_stream(hass, stream2.token) is stream2
    assert stream2.extension == "wav"
    result_data = b"".join([chunk async for chunk in stream2.async_stream_result()])
    assert result_data == data