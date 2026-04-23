async def test_camera_handle_mjpeg_stream(
    hass: HomeAssistant,
    mock_ring_client,
    mock_ring_devices,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test camera returns handle mjpeg stream when available."""
    await setup_platform(hass, Platform.CAMERA)

    front_camera_mock = mock_ring_devices.get_device(765432)
    front_camera_mock.async_recording_url.return_value = None

    state = hass.states.get("camera.front_last_recording")
    assert state is not None

    mock_request = make_mocked_request("GET", "/", headers={"token": "x"})

    # history not updated yet
    front_camera_mock.async_history.assert_not_called()
    front_camera_mock.async_recording_url.assert_not_called()
    stream = await async_get_mjpeg_stream(
        hass, mock_request, "camera.front_last_recording"
    )
    assert stream is None

    # Video url will be none so no  stream
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    front_camera_mock.async_history.assert_called_once()
    front_camera_mock.async_recording_url.assert_called()

    stream = await async_get_mjpeg_stream(
        hass, mock_request, "camera.front_last_recording"
    )
    assert stream is None

    # Stop the history updating so we can update the values manually
    front_camera_mock.async_history = AsyncMock()
    front_camera_mock.last_history[0]["recording"]["status"] = "not ready"
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    front_camera_mock.async_recording_url.assert_called()
    stream = await async_get_mjpeg_stream(
        hass, mock_request, "camera.front_last_recording"
    )
    assert stream is None

    # If the history id hasn't changed the camera will not check again for the video url
    # until the FORCE_REFRESH_INTERVAL has passed
    front_camera_mock.last_history[0]["recording"]["status"] = "ready"
    front_camera_mock.async_recording_url = AsyncMock(return_value="http://dummy.url")
    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    front_camera_mock.async_recording_url.assert_not_called()

    stream = await async_get_mjpeg_stream(
        hass, mock_request, "camera.front_last_recording"
    )
    assert stream is None

    freezer.tick(FORCE_REFRESH_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    front_camera_mock.async_recording_url.assert_called()

    # Now the stream should be returned
    stream_reader = MockStreamReader(SMALLEST_VALID_JPEG_BYTES)
    with patch("homeassistant.components.ring.camera.CameraMjpeg") as mock_camera:
        mock_camera.return_value.get_reader = AsyncMock(return_value=stream_reader)
        mock_camera.return_value.open_camera = AsyncMock()
        mock_camera.return_value.close = AsyncMock()

        stream = await async_get_mjpeg_stream(
            hass, mock_request, "camera.front_last_recording"
        )
        assert stream is not None
        # Check the stream has been read
        assert not await stream_reader.read(-1)