async def test_camera_single_image(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test a generic camera single image request."""
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

    def _mock_camera_image():
        mock_device.set_state(ESPHomeCameraState(key=1, data=SMALLEST_VALID_JPEG_BYTES))

    mock_client.request_single_image = _mock_camera_image

    client = await hass_client()
    resp = await client.get("/api/camera_proxy/camera.test_my_camera")
    await hass.async_block_till_done()
    state = hass.states.get("camera.test_my_camera")
    assert state is not None
    assert state.state == CameraState.IDLE

    assert resp.status == 200
    assert resp.content_type == "image/jpeg"
    assert resp.content_length == len(SMALLEST_VALID_JPEG_BYTES)
    assert await resp.read() == SMALLEST_VALID_JPEG_BYTES