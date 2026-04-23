async def test_fetching_in_async(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test async fetching of data."""
    tts_audio: asyncio.Future[bytes] = asyncio.Future()

    class EntityWithAsyncFetching(MockTTSEntity):
        """Entity that supports audio output option."""

        async def async_get_tts_audio(
            self, message: str, language: str, options: dict[str, Any]
        ) -> tts.TtsAudioType:
            return ("mp3", await tts_audio)

    await mock_config_entry_setup(hass, EntityWithAsyncFetching(DEFAULT_LANG))

    # Test async_get_media_source_audio
    media_source_id = tts.generate_media_source_id(
        hass,
        "test message",
        "tts.test",
        "en_US",
        cache=None,
    )

    task = hass.async_create_task(
        tts.async_get_media_source_audio(hass, media_source_id)
    )
    task2 = hass.async_create_task(
        tts.async_get_media_source_audio(hass, media_source_id)
    )

    url = await get_media_source_url(hass, media_source_id)
    client = await hass_client()
    client_get_task = hass.async_create_task(client.get(url))

    # Make sure that tasks are waiting for our future to resolve
    done, pending = await asyncio.wait((task, task2, client_get_task), timeout=0.1)
    assert len(done) == 0
    assert len(pending) == 3

    tts_audio.set_result(b"test")

    assert await task == ("mp3", b"test")
    assert await task2 == ("mp3", b"test")

    req = await client_get_task
    assert req.status == HTTPStatus.OK
    assert await req.read() == b"test"

    # Test error is not cached
    media_source_id = tts.generate_media_source_id(
        hass, "test message 2", "tts.test", "en_US", None, None
    )
    tts_audio = asyncio.Future()
    tts_audio.set_exception(HomeAssistantError("test error"))
    with pytest.raises(HomeAssistantError):
        assert await tts.async_get_media_source_audio(hass, media_source_id)

    tts_audio = asyncio.Future()
    tts_audio.set_result(b"test 2")
    assert await tts.async_get_media_source_audio(hass, media_source_id) == (
        "mp3",
        b"test 2",
    )