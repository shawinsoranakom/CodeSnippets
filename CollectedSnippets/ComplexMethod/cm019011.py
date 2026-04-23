async def test_tts_services(
    hass: HomeAssistant,
    cloud: MagicMock,
    hass_client: ClientSessionGenerator,
    service: str,
    service_data: dict[str, Any],
) -> None:
    """Test tts services."""
    calls = async_mock_service(hass, MP_DOMAIN, SERVICE_PLAY_MEDIA)
    mock_process_tts = AsyncMock(return_value=b"")
    cloud.voice.process_tts = mock_process_tts
    mock_process_tts_stream = _make_stream_mock("There is someone at the door.")
    cloud.voice.process_tts_stream = mock_process_tts_stream

    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    await cloud.login("test-user", "test-pass")
    client = await hass_client()

    await hass.services.async_call(
        domain=TTS_DOMAIN,
        service=service,
        service_data=service_data,
        blocking=True,
    )

    assert len(calls) == 1

    url = await get_media_source_url(hass, calls[0].data[ATTR_MEDIA_CONTENT_ID])
    await hass.async_block_till_done()
    response = await client.get(url)
    assert response.status == HTTPStatus.OK
    await hass.async_block_till_done()

    if service_data.get("entity_id", "").startswith("tts."):
        # Streaming
        assert mock_process_tts_stream.call_count == 1
        assert mock_process_tts_stream.call_args is not None
        assert (
            mock_process_tts_stream.call_args.kwargs["language"]
            == service_data[ATTR_LANGUAGE]
        )
        assert mock_process_tts_stream.call_args.kwargs["voice"] == "GadisNeural"
    else:
        # Non-streaming
        assert mock_process_tts.call_count == 1
        assert mock_process_tts.call_args is not None
        assert (
            mock_process_tts.call_args.kwargs["text"] == "There is someone at the door."
        )
        assert (
            mock_process_tts.call_args.kwargs["language"] == service_data[ATTR_LANGUAGE]
        )
        assert mock_process_tts.call_args.kwargs["voice"] == "GadisNeural"
        assert mock_process_tts.call_args.kwargs["output"] == "mp3"