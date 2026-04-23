async def test_light_onoff_mode_turn_on_off(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
) -> None:
    """Test ONOFF-only light turn on and off."""
    aioclient_mock.clear_requests()
    aioclient_mock.put(
        f"https://{config_entry_setup.data[CONF_HOST]}:1234"
        f"/api/s/{config_entry_setup.data[CONF_SITE_ID]}/rest/device/mock-id-4",
    )
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "light.device_led_no_rgb_led"},
        blocking=True,
    )

    assert aioclient_mock.call_count == 1
    call_data = aioclient_mock.mock_calls[0][2]
    assert call_data["led_override"] == "off"
    # Should not send brightness or color for ONOFF-only devices
    assert call_data.get("led_override_color_brightness") is None
    assert call_data.get("led_override_color") is None

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "light.device_led_no_rgb_led"},
        blocking=True,
    )

    assert aioclient_mock.call_count == 2
    call_data = aioclient_mock.mock_calls[1][2]
    assert call_data["led_override"] == "on"
    # Should not send brightness or color for ONOFF-only devices
    assert call_data.get("led_override_color_brightness") is None
    assert call_data.get("led_override_color") is None