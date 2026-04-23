async def test_enable_disable_motion_detection(
    hass: HomeAssistant, mock_remote, camera_info
) -> None:
    """Test enable and disable motion detection."""

    def set_recordmode(uuid, mode):
        """Set record mode."""
        motion_record_enabled = mode == "motion"
        camera_info["recordingSettings"]["motionRecordEnabled"] = motion_record_enabled

    mock_remote.return_value.set_recordmode.side_effect = set_recordmode
    config = {"platform": "uvc", "nvr": "foo", "key": "secret"}
    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert "motion_detection" not in state.attributes

    await hass.services.async_call(
        "camera", SERVICE_ENABLE_MOTION, {"entity_id": "camera.front"}, True
    )
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert state.attributes["motion_detection"]

    await hass.services.async_call(
        "camera", SERVICE_DISABLE_MOTION, {"entity_id": "camera.front"}, True
    )
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert "motion_detection" not in state.attributes

    mock_remote.return_value.set_recordmode.side_effect = nvr.NvrError

    await hass.services.async_call(
        "camera", SERVICE_ENABLE_MOTION, {"entity_id": "camera.front"}, True
    )
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert "motion_detection" not in state.attributes

    mock_remote.return_value.set_recordmode.side_effect = set_recordmode

    await hass.services.async_call(
        "camera", SERVICE_ENABLE_MOTION, {"entity_id": "camera.front"}, True
    )
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert state.attributes["motion_detection"]

    mock_remote.return_value.set_recordmode.side_effect = nvr.NvrError

    await hass.services.async_call(
        "camera", SERVICE_DISABLE_MOTION, {"entity_id": "camera.front"}, True
    )
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert state.attributes["motion_detection"]