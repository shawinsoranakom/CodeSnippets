async def test_legacy_resolving(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_provider: MSProvider,
    extra_options: str,
) -> None:
    """Test resolving legacy provider."""
    await mock_setup(hass, mock_provider)
    mock_get_tts_audio = mock_provider.get_tts_audio

    mock_provider.has_entity = True
    root = await media_source.async_browse_media(hass, "media-source://tts")
    assert len(root.children) == 0
    mock_provider.has_entity = False
    root = await media_source.async_browse_media(hass, "media-source://tts")
    assert len(root.children) == 1

    mock_get_tts_audio.reset_mock()
    media_id = "media-source://tts/test?message=Hello%20World"
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
        f"media-source://tts/test?message=Bye%20World&language=de_DE{extra_options}"
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