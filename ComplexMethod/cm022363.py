async def test_tts_service_speak_voice_settings(
    setup: AsyncMock,
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    capture_stream_calls,
    calls: list[ServiceCall],
    tts_service: str,
    service_data: dict[str, Any],
    mock_similarity: float,
) -> None:
    """Test tts service."""
    stream_calls, _, patch_stream = capture_stream_calls
    tts_entity = hass.data[tts.DOMAIN].get_entity(service_data[ATTR_ENTITY_ID])
    patch_stream(tts_entity)

    assert tts_entity._voice_settings == VoiceSettings(
        stability=DEFAULT_STABILITY,
        similarity_boost=DEFAULT_SIMILARITY / 2,
        style=DEFAULT_STYLE,
        use_speaker_boost=DEFAULT_USE_SPEAKER_BOOST,
    )

    await hass.services.async_call(
        tts.DOMAIN,
        tts_service,
        service_data,
        blocking=True,
    )

    assert (
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
        == HTTPStatus.OK
    )

    assert len(stream_calls) == 1
    language = service_data.get(tts.ATTR_LANGUAGE, tts_entity.default_language)
    call_kwargs = stream_calls[0]
    assert call_kwargs["text"] == "There is a person at the front door."
    assert call_kwargs["voice_id"] == "voice2"
    assert call_kwargs["model_id"] == "model1"
    assert call_kwargs["voice_settings"] == tts_entity._voice_settings
    assert call_kwargs["output_format"] == "mp3_44100_128"
    assert call_kwargs["language_code"] == language