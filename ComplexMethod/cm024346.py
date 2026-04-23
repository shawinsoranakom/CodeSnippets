async def test_resolving(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_tts_entity: MSEntity,
    extra_options: str,
) -> None:
    """Test resolving entity."""
    await mock_config_entry_setup(hass, mock_tts_entity)
    mock_get_tts_audio = mock_tts_entity.get_tts_audio

    mock_get_tts_audio.reset_mock()
    media_id = "media-source://tts/tts.test?message=Hello%20World"
    media = await media_source.async_resolve_media(hass, media_id, None)
    assert media.url.startswith("/api/tts_proxy/")
    assert media.mime_type == "audio/mpeg"
    assert await retrieve_media(hass, hass_client, media_id) == HTTPStatus.OK

    assert len(mock_get_tts_audio.mock_calls) == 1
    message, language = mock_get_tts_audio.mock_calls[0][1]
    assert message == "Hello World"
    assert language == "en_US"
    assert mock_get_tts_audio.mock_calls[0][2]["options"] == {}

    # Pass language and options
    mock_get_tts_audio.reset_mock()
    media_id = (
        f"media-source://tts/tts.test?message=Bye%20World&language=de_DE{extra_options}"
    )
    media = await media_source.async_resolve_media(hass, media_id, None)
    assert media.url.startswith("/api/tts_proxy/")
    assert media.mime_type == "audio/mpeg"
    assert await retrieve_media(hass, hass_client, media_id) == HTTPStatus.OK

    assert len(mock_get_tts_audio.mock_calls) == 1
    message, language = mock_get_tts_audio.mock_calls[0][1]
    assert message == "Bye World"
    assert language == "de_DE"
    assert mock_get_tts_audio.mock_calls[0][2]["options"] == {"voice": "Paulus"}

    # Test with result stream
    stream = MockResultStream(hass, "wav", b"")
    media = await media_source.async_resolve_media(hass, stream.media_source_id, None)
    assert media.url == stream.url
    assert media.mime_type == stream.content_type

    with pytest.raises(media_source.Unresolvable):
        await media_source.async_resolve_media(
            hass, "media-source://tts/-stream-/not-a-valid-token", None
        )