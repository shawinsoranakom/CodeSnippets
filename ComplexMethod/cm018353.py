async def test_stt_entity_properties(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test STT entity properties."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity("stt.openai_stt")
    assert entity is not None
    assert isinstance(entity.supported_languages, list)
    assert len(entity.supported_languages)
    assert stt.AudioFormats.WAV in entity.supported_formats
    assert stt.AudioFormats.OGG in entity.supported_formats
    assert stt.AudioCodecs.PCM in entity.supported_codecs
    assert stt.AudioCodecs.OPUS in entity.supported_codecs
    assert stt.AudioBitRates.BITRATE_8 in entity.supported_bit_rates
    assert stt.AudioBitRates.BITRATE_16 in entity.supported_bit_rates
    assert stt.AudioBitRates.BITRATE_24 in entity.supported_bit_rates
    assert stt.AudioBitRates.BITRATE_32 in entity.supported_bit_rates
    assert stt.AudioSampleRates.SAMPLERATE_8000 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_11000 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_18900 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_22000 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_32000 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_37800 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_44100 in entity.supported_sample_rates
    assert stt.AudioSampleRates.SAMPLERATE_48000 in entity.supported_sample_rates
    assert stt.AudioChannels.CHANNEL_MONO in entity.supported_channels
    assert stt.AudioChannels.CHANNEL_STEREO in entity.supported_channels