async def test_cover_position_range(
    hass: HomeAssistant,
) -> None:
    """Test cover discovery and position range using rangeController.

    Also tests an invalid cover position being handled correctly.
    """

    device = (
        "cover.test_range",
        "open",
        {
            "friendly_name": "Test cover range",
            "device_class": "blind",
            "supported_features": 7,
            "current_position": 30,
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

    _call, msg = await assert_request_calls_service(
        "Alexa.RangeController",
        "AdjustRangeValue",
        "cover#test_range",
        "cover.close_cover",
        hass,
        payload={"rangeValueDelta": -99, "rangeValueDeltaDefault": False},
        instance="cover.position",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "rangeValue"
    assert properties["namespace"] == "Alexa.RangeController"
    assert properties["value"] == 0

    await assert_range_changes(
        hass,
        [(25, -5, False), (35, 5, False), (50, 1, True), (10, -1, True)],
        "Alexa.RangeController",
        "AdjustRangeValue",
        "cover#test_range",
        "cover.set_cover_position",
        "position",
        instance="cover.position",
    )