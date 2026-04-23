async def test_supported_properties(
    hass: HomeAssistant,
    setup: AsyncMock,
) -> None:
    """Test the advertised capabilities of the ElevenLabs STT entity."""
    entity = stt.async_get_speech_to_text_engine(hass, "stt.elevenlabs_speech_to_text")
    assert entity is not None
    assert set(entity.supported_formats) == {stt.AudioFormats.WAV, stt.AudioFormats.OGG}
    assert set(entity.supported_codecs) == {stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS}
    assert set(entity.supported_bit_rates) == {stt.AudioBitRates.BITRATE_16}
    assert set(entity.supported_sample_rates) == {stt.AudioSampleRates.SAMPLERATE_16000}
    assert set(entity.supported_channels) == {
        stt.AudioChannels.CHANNEL_MONO,
        stt.AudioChannels.CHANNEL_STEREO,
    }
    assert "en-US" in entity.supported_languages