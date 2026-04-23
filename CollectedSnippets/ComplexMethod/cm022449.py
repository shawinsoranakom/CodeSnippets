async def test_color_setting_color_light(
    hass: HomeAssistant, supported_color_modes
) -> None:
    """Test ColorSpectrum trait support for light domain."""
    assert helpers.get_google_type(light.DOMAIN, None) is not None
    assert not trait.ColorSettingTrait.supported(light.DOMAIN, 0, None, {})
    assert trait.ColorSettingTrait.supported(
        light.DOMAIN, 0, None, {"supported_color_modes": supported_color_modes}
    )

    trt = trait.ColorSettingTrait(
        hass,
        State(
            "light.bla",
            STATE_ON,
            {
                light.ATTR_HS_COLOR: (20, 94),
                light.ATTR_BRIGHTNESS: 200,
                light.ATTR_COLOR_MODE: "hs",
                "supported_color_modes": supported_color_modes,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {"colorModel": "hsv"}

    assert trt.query_attributes() == {
        "color": {"spectrumHsv": {"hue": 20, "saturation": 0.94, "value": 200 / 255}}
    }

    assert trt.can_execute(
        trait.COMMAND_COLOR_ABSOLUTE, {"color": {"spectrumRGB": 16715792}}
    )

    calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
    await trt.execute(
        trait.COMMAND_COLOR_ABSOLUTE,
        BASIC_DATA,
        {"color": {"spectrumRGB": 1052927}},
        {},
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "light.bla",
        light.ATTR_HS_COLOR: (240, 93.725),
    }

    await trt.execute(
        trait.COMMAND_COLOR_ABSOLUTE,
        BASIC_DATA,
        {"color": {"spectrumHSV": {"hue": 100, "saturation": 0.50, "value": 0.20}}},
        {},
    )
    assert len(calls) == 2
    assert calls[1].data == {
        ATTR_ENTITY_ID: "light.bla",
        light.ATTR_HS_COLOR: [100, 50],
        light.ATTR_BRIGHTNESS: 0.2 * 255,
    }