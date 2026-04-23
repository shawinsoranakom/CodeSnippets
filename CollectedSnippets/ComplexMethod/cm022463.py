async def test_fan_speed(hass: HomeAssistant) -> None:
    """Test FanSpeed trait speed control support for fan domain."""
    assert helpers.get_google_type(fan.DOMAIN, None) is not None
    assert trait.FanSpeedTrait.supported(
        fan.DOMAIN, FanEntityFeature.SET_SPEED, None, None
    )

    trt = trait.FanSpeedTrait(
        hass,
        State(
            "fan.living_room_fan",
            STATE_ON,
            attributes={
                "percentage": 33,
                "percentage_step": 1.0,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "reversible": False,
        "supportsFanSpeedPercent": True,
    }

    assert trt.query_attributes() == {
        "currentFanSpeedPercent": 33,
    }

    assert trt.can_execute(trait.COMMAND_SET_FAN_SPEED, params={"fanSpeedPercent": 10})

    calls = async_mock_service(hass, fan.DOMAIN, fan.SERVICE_SET_PERCENTAGE)
    await trt.execute(
        trait.COMMAND_SET_FAN_SPEED, BASIC_DATA, {"fanSpeedPercent": 10}, {}
    )

    assert len(calls) == 1
    assert calls[0].data == {"entity_id": "fan.living_room_fan", "percentage": 10}