async def test_climate_fan_speed(hass: HomeAssistant) -> None:
    """Test FanSpeed trait speed control support for climate domain."""
    assert helpers.get_google_type(climate.DOMAIN, None) is not None
    assert trait.FanSpeedTrait.supported(
        climate.DOMAIN, ClimateEntityFeature.FAN_MODE, None, None
    )

    trt = trait.FanSpeedTrait(
        hass,
        State(
            "climate.living_room_ac",
            "on",
            attributes={
                "fan_modes": ["auto", "low", "medium", "high"],
                "fan_mode": "low",
            },
        ),
        BASIC_CONFIG,
    )

    assert trt.sync_attributes() == {
        "availableFanSpeeds": {
            "ordered": True,
            "speeds": [
                {
                    "speed_name": "auto",
                    "speed_values": [{"speed_synonym": ["auto"], "lang": "en"}],
                },
                {
                    "speed_name": "low",
                    "speed_values": [{"speed_synonym": ["low"], "lang": "en"}],
                },
                {
                    "speed_name": "medium",
                    "speed_values": [{"speed_synonym": ["medium"], "lang": "en"}],
                },
                {
                    "speed_name": "high",
                    "speed_values": [{"speed_synonym": ["high"], "lang": "en"}],
                },
            ],
        },
        "reversible": False,
    }

    assert trt.query_attributes() == {
        "currentFanSpeedSetting": "low",
    }

    assert trt.can_execute(trait.COMMAND_SET_FAN_SPEED, params={"fanSpeed": "medium"})

    calls = async_mock_service(hass, climate.DOMAIN, climate.SERVICE_SET_FAN_MODE)
    await trt.execute(
        trait.COMMAND_SET_FAN_SPEED, BASIC_DATA, {"fanSpeed": "medium"}, {}
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": "climate.living_room_ac",
        "fan_mode": "medium",
    }