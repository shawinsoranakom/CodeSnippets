async def test_support(hass: HomeAssistant, init_wyoming_stt) -> None:
    """Test supported properties."""
    state = hass.states.get("stt.test_asr")
    assert state is not None

    entity = stt.async_get_speech_to_text_entity(hass, "stt.test_asr")
    assert entity is not None

    assert entity.supported_languages == ["en-US"]
    assert entity.supported_formats == [stt.AudioFormats.WAV]
    assert entity.supported_codecs == [stt.AudioCodecs.PCM]
    assert entity.supported_bit_rates == [stt.AudioBitRates.BITRATE_16]
    assert entity.supported_sample_rates == [stt.AudioSampleRates.SAMPLERATE_16000]
    assert entity.supported_channels == [stt.AudioChannels.CHANNEL_MONO]