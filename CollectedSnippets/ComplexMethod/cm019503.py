async def test_setup_partial_config(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_remote
) -> None:
    """Test the setup with partial configuration."""
    config = {"platform": "uvc", "nvr": "foo", "key": "secret"}

    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    assert mock_remote.call_count == 1
    assert mock_remote.call_args == call("foo", 7080, "secret", ssl=False)

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