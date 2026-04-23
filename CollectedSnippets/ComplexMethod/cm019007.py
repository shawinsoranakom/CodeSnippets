async def test_tts_entity(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    entity_registry: EntityRegistry,
    cloud: MagicMock,
    mock_process_tts_side_effect: Exception | None,
) -> None:
    """Test text-to-speech entity."""
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
    entity_id = "tts.home_assistant_cloud"

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_UNKNOWN

    with patch(
        "homeassistant.components.tts.secrets.token_urlsafe", return_value="test_token"
    ):
        url = "/api/tts_get_url"
        data = {
            "engine_id": entity_id,
            "message": "There is someone at the door.",
        }

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

    assert mock_process_tts_stream.call_count == 1
    assert mock_process_tts_stream.call_args is not None
    assert mock_process_tts_stream.call_args.kwargs["language"] == "en-US"
    assert mock_process_tts_stream.call_args.kwargs["gender"] is None
    assert mock_process_tts_stream.call_args.kwargs["voice"] == "JennyNeural"

    state = hass.states.get(entity_id)
    assert state
    assert state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)

    # Test removing the entity
    entity_registry.async_remove(entity_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is None