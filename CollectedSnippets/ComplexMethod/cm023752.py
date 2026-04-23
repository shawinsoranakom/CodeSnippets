async def test_support(hass: HomeAssistant, init_wyoming_tts) -> None:
    """Test supported properties."""
    state = hass.states.get("tts.test_tts")
    assert state is not None

    entity = hass.data[DATA_INSTANCES]["tts"].get_entity("tts.test_tts")
    assert entity is not None

    assert entity.supported_languages == ["en-US"]
    assert entity.supported_options == [
        tts.ATTR_AUDIO_OUTPUT,
        tts.ATTR_VOICE,
        wyoming.ATTR_SPEAKER,
    ]
    voices = entity.async_get_supported_voices("en-US")
    assert len(voices) == 1
    assert voices[0].name == "Test Voice"
    assert voices[0].voice_id == "Test Voice"
    assert not entity.async_get_supported_voices("de-DE")