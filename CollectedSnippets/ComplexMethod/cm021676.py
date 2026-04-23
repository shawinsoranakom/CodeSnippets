async def test_initialize_camera_stream(
    hass: HomeAssistant, mock_camera: None, mock_stream: None
) -> None:
    """Test InitializeCameraStreams handler."""
    request = get_new_request(
        "Alexa.CameraStreamController", "InitializeCameraStreams", "camera#demo_camera"
    )

    await async_process_ha_core_config(
        hass, {"external_url": "https://mycamerastream.test"}
    )

    with patch(
        "homeassistant.components.demo.camera.DemoCamera.stream_source",
        return_value="rtsp://example.local",
    ):
        msg = await smart_home.async_handle_message(
            hass, get_default_config(hass), request
        )
        await hass.async_stop()

    assert "event" in msg
    response = msg["event"]
    assert response["header"]["namespace"] == "Alexa.CameraStreamController"
    assert response["header"]["name"] == "Response"
    camera_streams = response["payload"]["cameraStreams"]
    assert "https://mycamerastream.test/api/hls/" in camera_streams[0]["uri"]
    assert camera_streams[0]["protocol"] == "HLS"
    assert camera_streams[0]["resolution"]["width"] == 1280
    assert camera_streams[0]["resolution"]["height"] == 720
    assert camera_streams[0]["authorizationType"] == "NONE"
    assert camera_streams[0]["videoCodec"] == "H264"
    assert camera_streams[0]["audioCodec"] == "AAC"
    assert (
        "https://mycamerastream.test/api/camera_proxy/camera.demo_camera?token="
        in response["payload"]["imageUri"]
    )