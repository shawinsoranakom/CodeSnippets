async def test_stop_valve(
    hass: HomeAssistant, supported_features: ValveEntityFeature, state_controller: str
) -> None:
    """Test stop valve ToggleController."""
    device = (
        "valve.test",
        "opening",
        {
            "friendly_name": "Test valve",
            "supported_features": supported_features,
            "current_position": 30,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "valve#test"
    assert appliance["displayCategories"][0] == "OTHER"
    assert appliance["friendlyName"] == "Test valve"
    capabilities = assert_endpoint_capabilities(
        appliance,
        state_controller,
        "Alexa.ToggleController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    toggle_capability = get_capability(capabilities, "Alexa.ToggleController")
    assert toggle_capability is not None
    assert toggle_capability["instance"] == "valve.stop"

    properties = toggle_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "toggleState"} in properties["supported"]

    capability_resources = toggle_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "text",
        "value": {"text": "Stop", "locale": "en-US"},
    } in capability_resources["friendlyNames"]

    call, _ = await assert_request_calls_service(
        "Alexa.ToggleController",
        "TurnOn",
        "valve#test",
        "valve.stop_valve",
        hass,
        payload={},
        instance="valve.stop",
    )
    assert call.data["entity_id"] == "valve.test"
    assert call.service == SERVICE_STOP_VALVE