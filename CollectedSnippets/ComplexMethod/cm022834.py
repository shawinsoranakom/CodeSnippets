async def test_turn_on_color_no_fullcolorsupport(
    hass: HomeAssistant, fritz: Mock
) -> None:
    """Test turn device on in mapped color mode if unmapped is not supported."""
    device = FritzDeviceLightMock()
    device.get_color_temps.return_value = [2700, 6500]
    device.get_colors.return_value = {
        "Red": [("100", "70", "10"), ("100", "50", "10"), ("100", "30", "10")]
    }
    device.fullcolorsupport = False
    assert await setup_config_entry(
        hass, MOCK_CONFIG[DOMAIN][CONF_DEVICES][0], ENTITY_ID, device, fritz
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_BRIGHTNESS: 100, ATTR_HS_COLOR: (100, 70)},
        True,
    )
    assert device.set_state_on.call_count == 1
    assert device.set_level.call_count == 1
    assert device.set_color.call_count == 1
    assert device.set_unmapped_color.call_count == 0
    assert device.set_level.call_args_list == [call(100, True)]
    assert device.set_color.call_args_list == [call((100, 70), 0, True)]