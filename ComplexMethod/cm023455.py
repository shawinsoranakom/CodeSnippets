async def test_stt_entity_properties(hass: HomeAssistant) -> None:
    """Test STT entity properties."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(
        "stt.google_ai_stt"
    )
    assert entity is not None
    assert isinstance(entity.supported_languages, list)
    assert stt.AudioFormats.WAV in entity.supported_formats
    assert stt.AudioFormats.OGG in entity.supported_formats
    assert stt.AudioCodecs.PCM in entity.supported_codecs
    assert stt.AudioCodecs.OPUS in entity.supported_codecs
    assert stt.AudioBitRates.BITRATE_16 in entity.supported_bit_rates
    assert stt.AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates
    assert stt.AudioChannels.CHANNEL_MONO in entity.supported_channels