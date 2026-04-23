async def test_camera_stream(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test a generic camera stream."""
    entity_info = [
        CameraInfo(
            object_id="mycamera",
            key=1,
            name="my camera",
        )
    ]
    states = []
    user_service = []
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("camera.test_my_camera")
    assert state is not None
    assert state.state == CameraState.IDLE
    remaining_responses = 3

    def _mock_camera_image():
        nonlocal remaining_responses
        if remaining_responses == 0:
            return
        remaining_responses -= 1
        mock_device.set_state(ESPHomeCameraState(key=1, data=SMALLEST_VALID_JPEG_BYTES))

    mock_client.request_image_stream = _mock_camera_image
    mock_client.request_single_image = _mock_camera_image

    client = await hass_client()
    resp = await client.get("/api/camera_proxy_stream/camera.test_my_camera")
    await hass.async_block_till_done()
    state = hass.states.get("camera.test_my_camera")
    assert state is not None
    assert state.state == CameraState.IDLE

    assert resp.status == 200
    assert resp.content_type == "multipart/x-mixed-replace"
    assert resp.content_length is None
    raw_stream = b""
    async for data in resp.content.iter_any():
        raw_stream += data
        if len(raw_stream) > 300:
            break

    assert b"image/jpeg" in raw_stream