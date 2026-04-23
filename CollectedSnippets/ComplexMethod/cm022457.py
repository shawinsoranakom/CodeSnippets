async def test_humidity_setting_humidifier_setpoint(hass: HomeAssistant) -> None:
    """Test HumiditySetting trait support for humidifier domain - setpoint."""
    assert helpers.get_google_type(humidifier.DOMAIN, None) is not None
    assert trait.HumiditySettingTrait.supported(humidifier.DOMAIN, 0, None, None)

    trt = trait.HumiditySettingTrait(
        hass,
        State(
            "humidifier.bla",
            STATE_ON,
            {
                humidifier.ATTR_MIN_HUMIDITY: 20,
                humidifier.ATTR_MAX_HUMIDITY: 90,
                humidifier.ATTR_HUMIDITY: 38,
                humidifier.ATTR_CURRENT_HUMIDITY: 30,
            },
        ),
        BASIC_CONFIG,
    )
    assert trt.sync_attributes() == {
        "humiditySetpointRange": {"minPercent": 20, "maxPercent": 90}
    }
    assert trt.query_attributes() == {
        "humiditySetpointPercent": 38,
        "humidityAmbientPercent": 30,
    }
    assert trt.can_execute(trait.COMMAND_SET_HUMIDITY, {})

    calls = async_mock_service(hass, humidifier.DOMAIN, humidifier.SERVICE_SET_HUMIDITY)

    await trt.execute(trait.COMMAND_SET_HUMIDITY, BASIC_DATA, {"humidity": 32}, {})
    assert len(calls) == 1
    assert calls[0].data == {
        ATTR_ENTITY_ID: "humidifier.bla",
        humidifier.ATTR_HUMIDITY: 32,
    }