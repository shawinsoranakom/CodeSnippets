async def test_fan_speed_ordered(
    hass: HomeAssistant,
    percentage: int,
    percentage_step: float,
    speed: str,
    speeds: list[list[str]],
    percentage_result: int,
) -> None:
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
                "percentage": percentage,
                "percentage_step": percentage_step,
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "reversible": False,
        "supportsFanSpeedPercent": False,
        "availableFanSpeeds": {
            "ordered": True,
            "speeds": [
                {
                    "speed_name": f"{idx + 1}/{len(speeds)}",
                    "speed_values": [{"lang": "en", "speed_synonym": x}],
                }
                for idx, x in enumerate(speeds)
            ],
        },
    }

    assert trt.query_attributes() == {
        "currentFanSpeedSetting": speed,
    }

    assert trt.can_execute(trait.COMMAND_SET_FAN_SPEED, params={"fanSpeed": speed})

    calls = async_mock_service(hass, fan.DOMAIN, fan.SERVICE_SET_PERCENTAGE)
    await trt.execute(trait.COMMAND_SET_FAN_SPEED, BASIC_DATA, {"fanSpeed": speed}, {})

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "fan.living_room_fan",
        "percentage": percentage_result,
    }