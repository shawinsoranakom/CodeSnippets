async def test_oscillating_fan(hass: HomeAssistant) -> None:
    """Test oscillating fan with ToggleController."""
    device = (
        "fan.test_3",
        "off",
        {"friendly_name": "Test fan 3", "supported_features": 2},
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "fan#test_3"
    assert appliance["displayCategories"][0] == "FAN"
    assert appliance["friendlyName"] == "Test fan 3"
    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ToggleController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    toggle_capability = get_capability(capabilities, "Alexa.ToggleController")
    assert toggle_capability is not None
    assert toggle_capability["instance"] == "fan.oscillating"

    properties = toggle_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "toggleState"} in properties["supported"]

    capability_resources = toggle_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Oscillate"},
    } in capability_resources["friendlyNames"]

    call, _ = await assert_request_calls_service(
        "Alexa.ToggleController",
        "TurnOn",
        "fan#test_3",
        "fan.oscillate",
        hass,
        payload={},
        instance="fan.oscillating",
    )
    assert call.data["oscillating"]

    call, _ = await assert_request_calls_service(
        "Alexa.ToggleController",
        "TurnOff",
        "fan#test_3",
        "fan.oscillate",
        hass,
        payload={},
        instance="fan.oscillating",
    )
    assert not call.data["oscillating"]