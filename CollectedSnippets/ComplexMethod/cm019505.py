async def test_properties(hass: HomeAssistant, mock_remote) -> None:
    """Test the properties."""
    config = {"platform": "uvc", "nvr": "foo", "key": "secret"}
    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    camera_states = hass.states.async_all("camera")

    assert len(camera_states) == 2

    state = hass.states.get("camera.front")

    assert state
    assert state.name == "Front"
    assert state.state == CameraState.RECORDING
    assert state.attributes["brand"] == "Ubiquiti"
    assert state.attributes["model_name"] == "UVC"
    assert state.attributes["supported_features"] == CameraEntityFeature.STREAM