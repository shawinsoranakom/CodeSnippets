async def test_extending_stream_already_expired(
    hass: HomeAssistant,
    auth: FakeAuth,
    setup_platform: PlatformSetup,
    camera_device: None,
) -> None:
    """Test a API response when extending the stream returns an expired stream url."""
    now = utcnow()
    stream_1_expiration = now + datetime.timedelta(seconds=180)
    stream_2_expiration = now + datetime.timedelta(seconds=30)  # Will be in the past
    stream_3_expiration = now + datetime.timedelta(seconds=600)
    auth.responses = [
        make_stream_url_response(stream_1_expiration, token_num=1),
        make_stream_url_response(stream_2_expiration, token_num=2),
        make_stream_url_response(stream_3_expiration, token_num=3),
    ]
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    cam = hass.states.get("camera.my_camera")
    assert cam is not None
    assert cam.state == CameraState.STREAMING

    # The stream is expired, but we return it anyway
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.1.streamingToken"

    # Jump to when the stream will be refreshed
    await fire_alarm(hass, now + datetime.timedelta(seconds=160))
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.2.streamingToken"

    # The stream will have expired in the past, but 1 minute min refresh interval is applied.
    # The stream token is not updated.
    await fire_alarm(hass, now + datetime.timedelta(seconds=170))
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.2.streamingToken"

    # Now go past the min update interval and the stream is refreshed
    await fire_alarm(hass, now + datetime.timedelta(seconds=225))
    stream_source = await camera.async_get_stream_source(hass, "camera.my_camera")
    assert stream_source == "rtsp://some/url?auth=g.3.streamingToken"