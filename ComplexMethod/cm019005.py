async def test_get_tts_audio(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    cloud: MagicMock,
    data: dict[str, Any],
    expected_url_suffix: str,
    mock_process_tts_return_value: bytes | None,
    mock_process_tts_side_effect: Exception | None,
) -> None:
    """Test cloud provider."""
    mock_process_tts = AsyncMock(
        return_value=mock_process_tts_return_value,
        side_effect=mock_process_tts_side_effect,
    )
    cloud.voice.process_tts = mock_process_tts

    mock_process_tts_stream = _make_stream_mock("There is someone at the door.")
    if mock_process_tts_side_effect:
        mock_process_tts_stream.side_effect = mock_process_tts_side_effect
    cloud.voice.process_tts_stream = mock_process_tts_stream

    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    on_start_callback = cloud.register_on_start.call_args[0][0]
    await on_start_callback()
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

        # Force streaming
        await client.get(response["path"])

    if data.get("engine_id", "").startswith("tts."):
        # Streaming
        assert mock_process_tts_stream.call_count == 1
        assert mock_process_tts_stream.call_args is not None
        assert mock_process_tts_stream.call_args.kwargs["language"] == "en-US"
        assert mock_process_tts_stream.call_args.kwargs["gender"] is None
        assert mock_process_tts_stream.call_args.kwargs["voice"] == "JennyNeural"
    else:
        # Non-streaming
        assert mock_process_tts.call_count == 1
        assert mock_process_tts.call_args is not None
        assert (
            mock_process_tts.call_args.kwargs["text"] == "There is someone at the door."
        )
        assert mock_process_tts.call_args.kwargs["language"] == "en-US"
        assert mock_process_tts.call_args.kwargs["gender"] is None
        assert mock_process_tts.call_args.kwargs["voice"] == "JennyNeural"
        assert mock_process_tts.call_args.kwargs["output"] == "mp3"