async def test_direction_fan(hass: HomeAssistant) -> None:
    """Test fan direction with modeController."""
    device = (
        "fan.test_4",
        "on",
        {
            "friendly_name": "Test fan 4",
            "supported_features": 4,
            "direction": "forward",
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "fan#test_4"
    assert appliance["displayCategories"][0] == "FAN"
    assert appliance["friendlyName"] == "Test fan 4"
    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ModeController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    mode_capability = get_capability(capabilities, "Alexa.ModeController")
    assert mode_capability is not None
    assert mode_capability["instance"] == "fan.direction"

    properties = mode_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "mode"} in properties["supported"]

    capability_resources = mode_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Direction"},
    } in capability_resources["friendlyNames"]

    configuration = mode_capability["configuration"]
    assert configuration is not None
    assert configuration["ordered"] is False

    supported_modes = configuration["supportedModes"]
    assert supported_modes is not None
    assert {
        "value": "direction.forward",
        "modeResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "forward", "locale": "en-US"}}
            ]
        },
    } in supported_modes
    assert {
        "value": "direction.reverse",
        "modeResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "reverse", "locale": "en-US"}}
            ]
        },
    } in supported_modes

    call, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "fan#test_4",
        "fan.set_direction",
        hass,
        payload={"mode": "direction.reverse"},
        instance="fan.direction",
    )
    assert call.data["direction"] == "reverse"
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "direction.reverse"

    call, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "fan#test_4",
        "fan.set_direction",
        hass,
        payload={"mode": "direction.forward"},
        instance="fan.direction",
    )
    assert call.data["direction"] == "forward"
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "direction.forward"

    # Test for AdjustMode instance=None Error coverage
    with pytest.raises(AssertionError):
        call, _ = await assert_request_calls_service(
            "Alexa.ModeController",
            "AdjustMode",
            "fan#test_4",
            "fan.set_direction",
            hass,
            payload={},
            instance=None,
        )
    assert call.data