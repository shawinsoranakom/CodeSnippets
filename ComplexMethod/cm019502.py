async def test_setup_full_config(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_remote, camera_info
) -> None:
    """Test the setup with full configuration."""
    config = {
        "platform": "uvc",
        "nvr": "foo",
        "password": "bar",
        "port": 123,
        "key": "secret",
    }

    def mock_get_camera(uuid):
        """Create a mock camera."""
        if uuid == "id3":
            camera_info["model"] = "airCam"

        return camera_info

    mock_remote.return_value.index.return_value.append(
        {"uuid": "three", "name": "Old AirCam", "id": "id3"}
    )
    mock_remote.return_value.get_camera.side_effect = mock_get_camera

    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    assert mock_remote.call_count == 1
    assert mock_remote.call_args == call("foo", 123, "secret", ssl=False)

    camera_states = hass.states.async_all("camera")

    assert len(camera_states) == 2

    state = hass.states.get("camera.front")

    assert state
    assert state.name == "Front"

    state = hass.states.get("camera.back")

    assert state
    assert state.name == "Back"

    entity_entry = entity_registry.async_get("camera.front")

    assert entity_entry.unique_id == "id1"

    entity_entry = entity_registry.async_get("camera.back")

    assert entity_entry.unique_id == "id2"