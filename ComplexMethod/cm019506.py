async def test_motion_recording_mode_properties(
    hass: HomeAssistant, mock_remote
) -> None:
    """Test the properties."""
    config = {"platform": "uvc", "nvr": "foo", "key": "secret"}
    now = utcnow()
    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    state = hass.states.get("camera.front")

    assert state
    assert state.state == CameraState.RECORDING

    mock_remote.return_value.get_camera.return_value["recordingSettings"][
        "fullTimeRecordEnabled"
    ] = False
    mock_remote.return_value.get_camera.return_value["recordingSettings"][
        "motionRecordEnabled"
    ] = True

    async_fire_time_changed(hass, now + timedelta(seconds=31))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("camera.front")

    assert state
    assert state.state != CameraState.RECORDING
    assert state.attributes["last_recording_start_time"] == datetime(
        2021, 1, 8, 1, 56, 32, 367000, tzinfo=UTC
    )

    mock_remote.return_value.get_camera.return_value["recordingIndicator"] = "DISABLED"

    async_fire_time_changed(hass, now + timedelta(seconds=61))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("camera.front")

    assert state
    assert state.state != CameraState.RECORDING

    mock_remote.return_value.get_camera.return_value["recordingIndicator"] = (
        "MOTION_INPROGRESS"
    )

    async_fire_time_changed(hass, now + timedelta(seconds=91))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("camera.front")

    assert state
    assert state.state == CameraState.RECORDING

    mock_remote.return_value.get_camera.return_value["recordingIndicator"] = (
        "MOTION_FINISHED"
    )

    async_fire_time_changed(hass, now + timedelta(seconds=121))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get("camera.front")

    assert state
    assert state.state == CameraState.RECORDING