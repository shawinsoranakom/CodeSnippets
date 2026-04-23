async def test_cover_tilt_position(
    hass: HomeAssistant,
    tilt_position: int,
    tilt_position_attr_in_service_call: int | None,
    supported_features: CoverEntityFeature,
    service_call: str,
    stop_feature_enabled: bool,
) -> None:
    """Test cover discovery and tilt position using rangeController."""
    device = (
        "cover.test_tilt_range",
        "open",
        {
            "friendly_name": "Test cover tilt range",
            "device_class": "blind",
            "supported_features": supported_features,
            "tilt_position": tilt_position,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "cover#test_tilt_range"
    assert appliance["displayCategories"][0] == "INTERIOR_BLIND"
    assert appliance["friendlyName"] == "Test cover tilt range"

    expected_interfaces: dict[bool, list[str]] = {
        False: [
            "Alexa.PowerController",
            "Alexa.RangeController",
            "Alexa.EndpointHealth",
            "Alexa",
        ],
        True: [
            "Alexa.PowerController",
            "Alexa.RangeController",
            "Alexa.PlaybackController",
            "Alexa.EndpointHealth",
            "Alexa",
        ],
    }

    capabilities = assert_endpoint_capabilities(
        appliance, *expected_interfaces[stop_feature_enabled]
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

    call, msg = await assert_request_calls_service(
        "Alexa.RangeController",
        "SetRangeValue",
        "cover#test_tilt_range",
        service_call,
        hass,
        payload={"rangeValue": tilt_position},
        instance="cover.tilt",
    )
    assert call.data.get("tilt_position") == tilt_position_attr_in_service_call
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "rangeValue"
    assert properties["namespace"] == "Alexa.RangeController"
    assert properties["value"] == tilt_position