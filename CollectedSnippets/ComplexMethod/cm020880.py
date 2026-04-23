async def test_stream_source(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    hass_ws_client: WebSocketGenerator,
    fakeimgbytes_png: bytes,
) -> None:
    """Test that the stream source is rendered."""
    respx.get("http://example.com").respond(stream=fakeimgbytes_png)
    respx.get("http://example.com/0a").respond(stream=fakeimgbytes_png)

    hass.states.async_set("sensor.temp", "0")
    mock_entry = MockConfigEntry(
        title="config_test",
        domain=DOMAIN,
        data={},
        options={
            CONF_STILL_IMAGE_URL: "http://example.com",
            CONF_STREAM_SOURCE: 'http://example.com/{{ states.sensor.temp.state + "a" }}',
            CONF_LIMIT_REFETCH_TO_URL_CHANGE: True,
            CONF_FRAMERATE: 2,
            CONF_CONTENT_TYPE: "image/png",
            CONF_VERIFY_SSL: False,
            CONF_USERNAME: "barney",
            CONF_PASSWORD: "betty",
            CONF_RTSP_TRANSPORT: "http",
        },
    )
    mock_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_entry.entry_id)
    assert await async_setup_component(hass, "stream", {})
    await hass.async_block_till_done()

    hass.states.async_set("sensor.temp", "5")
    stream_source = await async_get_stream_source(hass, "camera.config_test")
    assert stream_source == "http://barney:betty@example.com/5a"

    # Create a mock stream that doesn't actually try to connect
    mock_stream = Mock()
    mock_stream.add_provider = Mock()
    mock_stream.start = AsyncMock()
    mock_stream.endpoint_url = Mock(return_value="http://home.assistant/playlist.m3u8")

    with patch(
        "homeassistant.components.camera.create_stream",
        return_value=mock_stream,
    ):
        # Request playlist through WebSocket
        client = await hass_ws_client(hass)

        await client.send_json(
            {"id": 1, "type": "camera/stream", "entity_id": "camera.config_test"}
        )
        msg = await client.receive_json()

        # Assert WebSocket response
        assert mock_stream.endpoint_url.call_count == 1
        assert msg["id"] == 1
        assert msg["type"] == TYPE_RESULT
        assert msg["success"]
        assert msg["result"]["url"][-13:] == "playlist.m3u8"