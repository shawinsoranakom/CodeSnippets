async def test_get_system_info_supervisor_not_available(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test the get system info when supervisor is not available."""
    hass.config.components.add("hassio")
    assert is_hassio(hass) is True
    with (
        patch("platform.system", return_value="Linux"),
        patch("homeassistant.helpers.system_info.is_docker_env", return_value=True),
        patch("homeassistant.helpers.system_info.is_official_image", return_value=True),
        patch("homeassistant.helpers.hassio.is_hassio", return_value=True),
        patch.object(hassio, "get_info", return_value=None),
        patch("homeassistant.helpers.system_info.cached_get_user", return_value="root"),
    ):
        info = await async_get_system_info(hass)
        assert isinstance(info, dict)
        assert info["version"] == current_version
        assert info["user"] is not None
        assert json.dumps(info) is not None
        assert info["installation_type"] == "Home Assistant Supervised"
        assert "No Home Assistant Supervisor info available" in caplog.text