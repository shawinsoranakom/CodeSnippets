async def test_login_tries_both_addrs_and_caches(
    hass: HomeAssistant, mock_remote, camera_v320, error
) -> None:
    """Test the login tries."""
    responses = [0]

    def mock_login(*a):
        """Mock login."""
        try:
            responses.pop(0)
            raise error
        except IndexError:
            pass

    snapshots = [0]

    def mock_snapshots(*a):
        """Mock get snapshots."""
        try:
            snapshots.pop(0)
            raise camera.CameraAuthError
        except IndexError:
            pass
        return "test_image"

    camera_v320.return_value.login.side_effect = mock_login

    config = {"platform": "uvc", "nvr": "foo", "key": "secret"}
    assert await async_setup_component(hass, "camera", {"camera": config})
    await hass.async_block_till_done()

    image = await async_get_image(hass, "camera.front")

    assert camera_v320.call_count == 2
    assert camera_v320.call_args == call("host-b", "admin", "ubnt")
    assert image.content_type == DEFAULT_CONTENT_TYPE
    assert image.content == "test_image"

    camera_v320.reset_mock()
    camera_v320.return_value.get_snapshot.side_effect = mock_snapshots

    image = await async_get_image(hass, "camera.front")

    assert camera_v320.call_count == 1
    assert camera_v320.call_args == call("host-b", "admin", "ubnt")
    assert camera_v320.return_value.login.call_count == 1
    assert image.content_type == DEFAULT_CONTENT_TYPE
    assert image.content == "test_image"