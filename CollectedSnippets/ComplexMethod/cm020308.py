async def test_refresh_expired_stream_failure(
    hass: HomeAssistant,
    auth: FakeAuth,
    setup_platform: PlatformSetup,
    camera_device: None,
) -> None:
    """Tests a failure when refreshing the stream."""
    now = utcnow()
    stream_1_expiration = now + datetime.timedelta(seconds=90)
    stream_2_expiration = now + datetime.timedelta(seconds=180)
    auth.responses = [
        make_stream_url_response(expiration=stream_1_expiration, token_num=1),
        # Extending the stream fails with arbitrary error
        aiohttp.web.Response(status=HTTPStatus.INTERNAL_SERVER_ERROR),
        # Next attempt to get a stream fetches a new url
        make_stream_url_response(expiration=stream_2_expiration, token_num=2),
    ]
    await setup_platform()
    assert await async_setup_component(hass, "stream", {})

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

    # Request an HLS stream
    with patch("homeassistant.components.camera.create_stream") as create_stream:
        create_stream.return_value.start = AsyncMock()
        create_stream.return_value.stop = AsyncMock()
        hls_url = await camera.async_request_stream(hass, "camera.my_camera", fmt="hls")
        assert hls_url.startswith("/api/hls/")  # Includes access token
        assert create_stream.called

    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.1.streamingToken"

    # Fire alarm when stream is nearing expiration, causing it to be extended.
    # The stream expires.
    next_update = now + datetime.timedelta(seconds=65)
    await fire_alarm(hass, next_update)

    # The stream is entirely refreshed
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.2.streamingToken"

    # Requesting an HLS stream will create an entirely new stream
    with patch("homeassistant.components.camera.create_stream") as create_stream:
        create_stream.return_value.start = AsyncMock()
        # The HLS stream endpoint was invalidated, with a new auth token
        hls_url2 = await camera.async_request_stream(
            hass, "camera.my_camera", fmt="hls"
        )
        assert hls_url != hls_url2
        assert hls_url2.startswith("/api/hls/")  # Includes access token
        assert create_stream.called