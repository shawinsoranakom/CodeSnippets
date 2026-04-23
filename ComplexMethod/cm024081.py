async def test_camera_active_job(
    hass: HomeAssistant,
    mock_config_entry,
    mock_api,
    mock_job_api_printing,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test camera while job active."""
    assert await async_setup_component(hass, "prusalink", {})
    state = hass.states.get("camera.mock_title_preview")
    assert state is not None
    assert state.state == "idle"

    client = await hass_client()

    with patch("pyprusalink.PrusaLink.get_file", return_value=b"hello"):
        resp = await client.get("/api/camera_proxy/camera.mock_title_preview")
        assert resp.status == 200
        assert await resp.read() == b"hello"

    # Make sure we hit cached value.
    with patch("pyprusalink.PrusaLink.get_file", side_effect=ValueError):
        resp = await client.get("/api/camera_proxy/camera.mock_title_preview")
        assert resp.status == 200
        assert await resp.read() == b"hello"