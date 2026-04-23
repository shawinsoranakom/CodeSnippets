async def test_detect_radio_type_success_with_settings(
    znp_probe, zigate_probe, deconz_probe, bellows_probe, hass: HomeAssistant
) -> None:
    """Test detect radios successfully but probing returns new settings."""

    handler = config_flow.ZhaConfigFlowHandler()
    handler._radio_mgr.device_path = "/dev/null"
    handler.hass = hass

    await handler._radio_mgr.detect_radio_type()

    assert handler._radio_mgr.radio_type == RadioType.ezsp
    assert handler._radio_mgr.device_settings["new_setting"] == 123
    assert (
        handler._radio_mgr.device_settings[zigpy.config.CONF_DEVICE_PATH] == "/dev/null"
    )

    assert bellows_probe.await_count == 1
    assert znp_probe.await_count == 0
    assert deconz_probe.await_count == 0
    assert zigate_probe.await_count == 0