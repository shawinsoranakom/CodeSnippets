async def test_cover_tilt_position_range(hass: HomeAssistant) -> None:
    """Test cover discovery and tilt position range using rangeController.

    Also tests and invalid tilt position being handled correctly.
    """
    device = (
        "cover.test_tilt_range",
        "open",
        {
            "friendly_name": "Test cover tilt range",
            "device_class": "blind",
            "supported_features": 240,
            "tilt_position": 30,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "cover#test_tilt_range"
    assert appliance["displayCategories"][0] == "INTERIOR_BLIND"
    assert appliance["friendlyName"] == "Test cover tilt range"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.RangeController",
        "Alexa.PlaybackController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    range_capability = get_capability(capabilities, "Alexa.RangeController")
    assert range_capability is not None
    assert range_capability["instance"] == "cover.tilt"

    semantics = range_capability["semantics"]
    assert semantics is not None

    action_mappings = semantics["actionMappings"]
    assert action_mappings is not None

    state_mappings = semantics["stateMappings"]
    assert state_mappings is not None

    call, _ = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "cover#test_tilt_range",
        "cover.set_cover_tilt_position",
        hass,
        payload={"rangeValue": 50},
        instance="cover.tilt",
    )
    assert call.data["tilt_position"] == 50

    call, msg = await assert_request_calls_service(
        "Alexa.RangeController",
        "AdjustRangeValue",
        "cover#test_tilt_range",
        "cover.close_cover_tilt",
        hass,
        payload={"rangeValueDelta": -99, "rangeValueDeltaDefault": False},
        instance="cover.tilt",
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
        "cover#test_tilt_range",
        "cover.set_cover_tilt_position",
        "tilt_position",
        instance="cover.tilt",
    )