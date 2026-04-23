async def test_stt_process_audio_stream_success(
    hass: HomeAssistant,
    mock_genai_client: AsyncMock,
    audio_format: stt.AudioFormats,
    call_convert_to_wav: bool,
) -> None:
    """Test STT processing audio stream successfully."""
    entity = hass.data[stt.DOMAIN].get_entity("stt.google_ai_stt")

    metadata = stt.SpeechMetadata(
        language="en-US",
        format=audio_format,
        codec=stt.AudioCodecs.PCM,
        bit_rate=stt.AudioBitRates.BITRATE_16,
        sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
        channel=stt.AudioChannels.CHANNEL_MONO,
    )
    audio_stream = _async_get_audio_stream(b"test_audio_bytes")

    with patch(
        "homeassistant.components.google_generative_ai_conversation.stt.convert_to_wav",
        return_value=b"converted_wav_bytes",
    ) as mock_convert_to_wav:
        result = await entity.async_process_audio_stream(metadata, audio_stream)

    assert result.result == stt.SpeechResultState.SUCCESS
    assert result.text == "This is a test transcription."

    if call_convert_to_wav:
        mock_convert_to_wav.assert_called_once_with(
            b"test_audio_bytes", "audio/L16;rate=16000"
        )
    else:
        mock_convert_to_wav.assert_not_called()

    mock_genai_client.aio.models.generate_content.assert_called_once()
    call_args = mock_genai_client.aio.models.generate_content.call_args
    assert call_args.kwargs["model"] == TEST_CHAT_MODEL

    contents = call_args.kwargs["contents"]
    assert contents[0] == TEST_PROMPT
    assert isinstance(contents[1], types.Part)
    assert contents[1].inline_data.mime_type == f"audio/{audio_format.value}"
    if call_convert_to_wav:
        assert contents[1].inline_data.data == b"converted_wav_bytes"
    else:
        assert contents[1].inline_data.data == b"test_audio_bytes"