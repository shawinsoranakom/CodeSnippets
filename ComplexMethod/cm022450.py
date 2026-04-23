async def test_color_setting_temperature_light(hass: HomeAssistant) -> None:
    """Test ColorTemperature trait support for light domain."""
    assert helpers.get_google_type(light.DOMAIN, None) is not None
    assert not trait.ColorSettingTrait.supported(light.DOMAIN, 0, None, {})
    assert trait.ColorSettingTrait.supported(
        light.DOMAIN, 0, None, {"supported_color_modes": ["color_temp"]}
    )

    trt = trait.ColorSettingTrait(
        hass,
        State(
            "light.bla",
            STATE_ON,
            {
                light.ATTR_MAX_COLOR_TEMP_KELVIN: 5000,
                light.ATTR_COLOR_MODE: "color_temp",
                light.ATTR_COLOR_TEMP_KELVIN: 3333,
                light.ATTR_MIN_COLOR_TEMP_KELVIN: 2000,
                "supported_color_modes": ["color_temp"],
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "colorTemperatureRange": {"temperatureMinK": 2000, "temperatureMaxK": 5000}
    }

    assert trt.query_attributes() == {"color": {"temperatureK": 3333}}

    assert trt.can_execute(
        trait.COMMAND_COLOR_ABSOLUTE, {"color": {"temperature": 400}}
    )
    calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)

    with pytest.raises(helpers.SmartHomeError) as err:
        await trt.execute(
            trait.COMMAND_COLOR_ABSOLUTE,
            BASIC_DATA,
            {"color": {"temperature": 5555}},
            {},
        )
    assert err.value.code == const.ERR_VALUE_OUT_OF_RANGE

    await trt.execute(
        trait.COMMAND_COLOR_ABSOLUTE, BASIC_DATA, {"color": {"temperature": 2857}}, {}
    )
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "light.bla",
        light.ATTR_COLOR_TEMP_KELVIN: 2857,
    }