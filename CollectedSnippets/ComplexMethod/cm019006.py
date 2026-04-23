async def test_get_tts_audio_logged_out(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    cloud: MagicMock,
    data: dict[str, Any],
    expected_url_suffix: str,
) -> None:
    """Test cloud get tts audio when user is logged out."""
    mock_process_tts = AsyncMock(
        side_effect=VoiceTokenError("No token!"),
    )
    cloud.voice.process_tts = mock_process_tts
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    client = await hass_client()

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
        url = "/api/tts_get_url"
        data |= {"message": "There is someone at the door."}

        req = await client.post(url, json=data)
        assert req.status == HTTPStatus.OK
        response = await req.json()

        assert response == {
            "url": ("http://example.local:8123/api/tts_proxy/test_token.mp3"),
            "path": ("/api/tts_proxy/test_token.mp3"),
        }
        await hass.async_block_till_done()

    assert mock_process_tts.call_count == 1
    assert mock_process_tts.call_args is not None
    assert mock_process_tts.call_args.kwargs["text"] == "There is someone at the door."
    assert mock_process_tts.call_args.kwargs["language"] == "en-US"
    assert mock_process_tts.call_args.kwargs["gender"] is None
    assert mock_process_tts.call_args.kwargs["voice"] == "JennyNeural"
    assert mock_process_tts.call_args.kwargs["output"] == "mp3"