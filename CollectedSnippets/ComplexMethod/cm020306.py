async def test_refresh_expired_stream_token(
    hass: HomeAssistant,
    setup_platform: PlatformSetup,
    auth: FakeAuth,
    camera_device: None,
) -> None:
    """Test a camera stream expiration and refresh."""
    now = utcnow()
    stream_1_expiration = now + datetime.timedelta(seconds=90)
    stream_2_expiration = now + datetime.timedelta(seconds=180)
    stream_3_expiration = now + datetime.timedelta(seconds=360)
    auth.responses = [
        # Stream URL #1
        make_stream_url_response(stream_1_expiration, token_num=1),
        # Stream URL #2
        make_stream_url_response(stream_2_expiration, token_num=2),
        # Stream URL #3
        make_stream_url_response(stream_3_expiration, token_num=3),
    ]
    await setup_platform()
    assert await async_setup_component(hass, "stream", {})

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

    # Request a stream for the camera entity to exercise nest cam + camera interaction
    # and shutdown on url expiration
    with patch("homeassistant.components.camera.create_stream") as create_stream:
        create_stream.return_value.start = AsyncMock()
        hls_url = await camera.async_request_stream(hass, "camera.my_camera", fmt="hls")
        assert hls_url.startswith("/api/hls/")  # Includes access token
        assert create_stream.called

    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.1.streamingToken"

    # Fire alarm before stream_1_expiration. The stream url is not refreshed
    next_update = now + datetime.timedelta(seconds=25)
    await fire_alarm(hass, next_update)
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.1.streamingToken"

    # Alarm is near stream_1_expiration which causes the stream extension
    next_update = now + datetime.timedelta(seconds=65)
    await fire_alarm(hass, next_update)
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.2.streamingToken"

    # HLS stream is not re-created, just the source is updated
    with patch("homeassistant.components.camera.create_stream") as create_stream:
        hls_url1 = await camera.async_request_stream(
            hass, "camera.my_camera", fmt="hls"
        )
        assert hls_url == hls_url1

    # Next alarm is well before stream_2_expiration, no change
    next_update = now + datetime.timedelta(seconds=100)
    await fire_alarm(hass, next_update)
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.2.streamingToken"

    # Alarm is near stream_2_expiration, causing it to be extended
    next_update = now + datetime.timedelta(seconds=155)
    await fire_alarm(hass, next_update)
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.3.streamingToken"

    # HLS stream is still not re-created
    with patch("homeassistant.components.camera.create_stream") as create_stream:
        hls_url2 = await camera.async_request_stream(
            hass, "camera.my_camera", fmt="hls"
        )
        assert hls_url == hls_url2