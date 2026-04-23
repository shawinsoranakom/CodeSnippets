async def test_vacuum_fan_speed(hass: HomeAssistant) -> None:
    """Test vacuum fan speed with rangeController."""
    device = (
        "vacuum.test_2",
        "cleaning",
        {
            "friendly_name": "Test vacuum 2",
            "supported_features": VacuumEntityFeature.TURN_ON
            | VacuumEntityFeature.TURN_OFF
            | VacuumEntityFeature.START
            | VacuumEntityFeature.STOP
            | VacuumEntityFeature.PAUSE
            | VacuumEntityFeature.FAN_SPEED,
            "fan_speed_list": ["off", "low", "medium", "high", "turbo", "super_sucker"],
            "fan_speed": "medium",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "vacuum#test_2"
    assert appliance["displayCategories"][0] == "VACUUM_CLEANER"
    assert appliance["friendlyName"] == "Test vacuum 2"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.RangeController",
        "Alexa.TimeHoldController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    range_capability = get_capability(capabilities, "Alexa.RangeController")
    assert range_capability is not None
    assert range_capability["instance"] == "vacuum.fan_speed"

    capability_resources = range_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.FanSpeed"},
    } in capability_resources["friendlyNames"]

    configuration = range_capability["configuration"]
    assert configuration is not None

    supported_range = configuration["supportedRange"]
    assert supported_range["minimumValue"] == 0
    assert supported_range["maximumValue"] == 5
    assert supported_range["precision"] == 1

    presets = configuration["presets"]
    assert {
        "rangeValue": 0,
        "presetResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "off", "locale": "en-US"}}
            ]
        },
    } in presets

    assert {
        "rangeValue": 1,
        "presetResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "low", "locale": "en-US"}},
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Minimum"}},
            ]
        },
    } in presets

    assert {
        "rangeValue": 2,
        "presetResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "medium", "locale": "en-US"}}
            ]
        },
    } in presets

    assert {
        "rangeValue": 5,
        "presetResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "super sucker", "locale": "en-US"}},
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Maximum"}},
            ]
        },
    } in presets

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "vacuum#test_2",
        "vacuum.set_fan_speed",
        hass,
        payload={"rangeValue": 1},
        instance="vacuum.fan_speed",
    )
    assert call.data["fan_speed"] == "low"

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "vacuum#test_2",
        "vacuum.set_fan_speed",
        hass,
        payload={"rangeValue": 5},
        instance="vacuum.fan_speed",
    )
    assert call.data["fan_speed"] == "super_sucker"

    await assert_range_changes(
        hass,
        [
            ("low", -1, False),
            ("high", 1, False),
            ("medium", 0, False),
            ("super_sucker", 99, False),
        ],
        "Alexa.RangeController",
        "AdjustRangeValue",
        "vacuum#test_2",
        "vacuum.set_fan_speed",
        "fan_speed",
        instance="vacuum.fan_speed",
    )