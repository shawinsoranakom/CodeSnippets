async def test_tts(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_create_speech: MagicMock,
    entity_registry: er.EntityRegistry,
    calls: list[ServiceCall],
    service_data: dict[str, Any],
) -> None:
    """Test text to speech generation."""
    entity_id = "tts.openai_tts"

    # Ensure entity is linked to the subentry
    entity_entry = entity_registry.async_get(entity_id)
    tts_entry = next(
        iter(
            entry
            for entry in mock_config_entry.subentries.values()
            if entry.subentry_type == "tts"
        )
    )
    assert entity_entry is not None
    assert entity_entry.config_entry_id == mock_config_entry.entry_id
    assert entity_entry.config_subentry_id == tts_entry.subentry_id

    # Mock the OpenAI response stream
    mock_create_speech.return_value = [b"mock aud", b"io data"]

    await hass.services.async_call(
        tts.DOMAIN,
        "speak",
        service_data,
        blocking=True,
    )

    assert len(calls) == 1
    assert (
        await retrieve_media(hass, hass_client, calls[0].data[ATTR_MEDIA_CONTENT_ID])
        == HTTPStatus.OK
    )
    voice_id = service_data[tts.ATTR_OPTIONS].get(tts.ATTR_VOICE, "marin")
    mock_create_speech.assert_called_once_with(
        model="gpt-4o-mini-tts",
        voice=voice_id,
        input="There is a person at the front door.",
        instructions="",
        speed=1.0,
        response_format="mp3",
    )