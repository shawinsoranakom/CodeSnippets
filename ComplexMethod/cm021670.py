async def test_cover_semantics_position_and_tilt(hass: HomeAssistant) -> None:
    """Test cover discovery and semantics with position and tilt support."""
    device = (
        "cover.test_semantics",
        "open",
        {
            "friendly_name": "Test cover semantics",
            "device_class": "blind",
            "supported_features": 255,
            "current_position": 30,
            "tilt_position": 30,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "cover#test_semantics"
    assert appliance["displayCategories"][0] == "INTERIOR_BLIND"
    assert appliance["friendlyName"] == "Test cover semantics"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.RangeController",
        "Alexa.PlaybackController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    playback_controller_capability = get_capability(
        capabilities, "Alexa.PlaybackController"
    )
    assert playback_controller_capability is not None
    assert playback_controller_capability["supportedOperations"] == ["Stop"]

    # Assert both the cover and tilt stop calls are invoked
    stop_cover_tilt_calls = async_mock_service(hass, "cover", "stop_cover_tilt")
    await assert_request_calls_service(
        "Alexa.PlaybackController",
        "Stop",
        "cover#test_semantics",
        "cover.stop_cover",
        hass,
    )
    assert len(stop_cover_tilt_calls) == 1
    call = stop_cover_tilt_calls[0]
    assert call.data == {"entity_id": "cover.test_semantics"}

    # Assert for Position Semantics
    position_capability = get_capability(
        capabilities, "Alexa.RangeController", "cover.position"
    )
    position_semantics = position_capability["semantics"]
    assert position_semantics is not None

    position_action_mappings = position_semantics["actionMappings"]
    assert position_action_mappings is not None
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Lower"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 0}},
    } in position_action_mappings
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Raise"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 100}},
    } in position_action_mappings

    # Assert for Tilt Semantics
    tilt_capability = get_capability(
        capabilities, "Alexa.RangeController", "cover.tilt"
    )
    tilt_semantics = tilt_capability["semantics"]
    assert tilt_semantics is not None
    tilt_action_mappings = tilt_semantics["actionMappings"]
    assert tilt_action_mappings is not None
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Close"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 0}},
    } in tilt_action_mappings
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Open"],
        "directive": {"name": "SetRangeValue", "payload": {"rangeValue": 100}},
    } in tilt_action_mappings

    tilt_state_mappings = tilt_semantics["stateMappings"]
    assert tilt_state_mappings is not None
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Closed"],
        "value": 0,
    } in tilt_state_mappings
    assert {
        "@type": "StatesToRange",
        "states": ["Alexa.States.Open"],
        "range": {"minimumValue": 1, "maximumValue": 100},
    } in tilt_state_mappings