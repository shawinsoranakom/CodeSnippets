async def test_service_register(hass: HomeAssistant) -> None:
    """Check if service will be setup."""
    assert await async_setup_component(hass, "hassio", {})
    # New app services
    assert hass.services.has_service("hassio", "app_start")
    assert hass.services.has_service("hassio", "app_stop")
    assert hass.services.has_service("hassio", "app_restart")
    assert hass.services.has_service("hassio", "app_stdin")
    # Legacy addon services (deprecated)
    assert hass.services.has_service("hassio", "addon_start")
    assert hass.services.has_service("hassio", "addon_stop")
    assert hass.services.has_service("hassio", "addon_restart")
    assert hass.services.has_service("hassio", "addon_stdin")
    # Other services
    assert hass.services.has_service("hassio", "host_shutdown")
    assert hass.services.has_service("hassio", "host_reboot")
    assert hass.services.has_service("hassio", "host_reboot")
    assert hass.services.has_service("hassio", "backup_full")
    assert hass.services.has_service("hassio", "backup_partial")
    assert hass.services.has_service("hassio", "restore_full")
    assert hass.services.has_service("hassio", "restore_partial")
    assert hass.services.has_service("hassio", "mount_reload")