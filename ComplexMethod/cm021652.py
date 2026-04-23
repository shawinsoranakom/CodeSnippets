async def test_cover_position(
    hass: HomeAssistant,
    position: int,
    position_attr_in_service_call: int | None,
    supported_features: CoverEntityFeature,
    service_call: str,
) -> None:
    """Test cover discovery and position using rangeController."""
    device = (
        "cover.test_range",
        "open",
        {
            "friendly_name": "Test cover range",
            "device_class": "blind",
            "supported_features": supported_features,
            "current_position": position,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "cover#test_range"
    assert appliance["displayCategories"][0] == "INTERIOR_BLIND"
    assert appliance["friendlyName"] == "Test cover range"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.RangeController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    range_capability = get_capability(capabilities, "Alexa.RangeController")
    assert range_capability is not None
    assert range_capability["instance"] == "cover.position"

    properties = range_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "rangeValue"} in properties["supported"]

    capability_resources = range_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "text",
        "value": {"text": "Position", "locale": "en-US"},
    } in capability_resources["friendlyNames"]

    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Opening"},
    } in capability_resources["friendlyNames"]

    configuration = range_capability["configuration"]
    assert configuration is not None
    assert configuration["unitOfMeasure"] == "Alexa.Unit.Percent"

    supported_range = configuration["supportedRange"]
    assert supported_range["minimumValue"] == 0
    assert supported_range["maximumValue"] == 100
    assert supported_range["precision"] == 1

    # Assert for Position Semantics
    position_semantics = range_capability["semantics"]
    assert position_semantics is not None

    position_action_mappings = position_semantics["actionMappings"]
    assert position_action_mappings is not None
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Lower", "Alexa.Actions.Close"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 0}},
    } in position_action_mappings
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Raise", "Alexa.Actions.Open"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 100}},
    } in position_action_mappings

    position_state_mappings = position_semantics["stateMappings"]
    assert position_state_mappings is not None
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Closed"],
        "value": 0,
    } in position_state_mappings
    assert {
        "@type": "StatesToRange",
        "states": ["Alexa.States.Open"],
        "range": {"minimumValue": 1, "maximumValue": 100},
    } in position_state_mappings

    call, msg = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "cover#test_range",
        service_call,
        hass,
        payload={"rangeValue": position},
        instance="cover.position",
    )
    assert call.data.get("position") == position_attr_in_service_call
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "rangeValue"
    assert properties["namespace"] == "Alexa.RangeController"
    assert properties["value"] == position