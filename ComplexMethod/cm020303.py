async def test_camera_device(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    setup_platform: PlatformSetup,
    camera_device: None,
) -> None:
    """Test a basic camera with a live stream."""
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.my_camera")
    assert camera is not None
    assert camera.state == CameraState.STREAMING
    assert camera.attributes.get(ATTR_FRIENDLY_NAME) == "My Camera"

    entry = entity_registry.async_get("camera.my_camera")
    assert entry.unique_id == f"{DEVICE_ID}-camera"
    assert entry.domain == "camera"

    device = device_registry.async_get(entry.device_id)
    assert device.name == "My Camera"
    assert device.model == "Camera"
    assert device.identifiers == {("nest", DEVICE_ID)}