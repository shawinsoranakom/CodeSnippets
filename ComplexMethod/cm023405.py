async def test_hls_stream(
    hass: HomeAssistant, setup_component, hls_stream, stream_worker_sync, h264_video
) -> None:
    """Test hls stream.

    Purposefully not mocking anything here to test full
    integration with the stream component.
    """

    stream_worker_sync.pause()

    # Setup demo HLS track
    stream = create_stream(hass, h264_video, {}, dynamic_stream_settings())

    # Request stream
    stream.add_provider(HLS_PROVIDER)
    await stream.start()

    hls_client = await hls_stream(stream)

    # Fetch master playlist
    master_playlist_response = await hls_client.get()
    assert master_playlist_response.status == HTTPStatus.OK

    # Fetch init
    master_playlist = await master_playlist_response.text()
    init_response = await hls_client.get("/init.mp4")
    assert init_response.status == HTTPStatus.OK

    # Fetch playlist
    playlist_url = "/" + master_playlist.splitlines()[-1]
    playlist_response = await hls_client.get(playlist_url)
    assert playlist_response.status == HTTPStatus.OK

    # Fetch segment
    playlist = await playlist_response.text()
    segment_url = "/" + [line for line in playlist.splitlines() if line][-1]
    segment_response = await hls_client.get(segment_url)
    assert segment_response.status == HTTPStatus.OK

    stream_worker_sync.resume()

    # Stop stream, if it hasn't quit already
    await stream.stop()

    # Ensure playlist not accessible after stream ends
    fail_response = await hls_client.get()
    assert fail_response.status == HTTPStatus.NOT_FOUND

    assert stream.get_diagnostics() == {
        "container_format": "mov,mp4,m4a,3gp,3g2,mj2",
        "keepalive": False,
        "orientation": Orientation.NO_TRANSFORM,
        "start_worker": 1,
        "video_codec": "h264",
        "worker_error": 1,
    }