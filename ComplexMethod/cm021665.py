async def test_valve_position_mode(hass: HomeAssistant) -> None:
    """Test valve discovery and position using modeController."""
    device = (
        "valve.test_mode",
        "open",
        {
            "friendly_name": "Test valve mode",
            "device_class": "water",
            "supported_features": ValveEntityFeature.OPEN
            | ValveEntityFeature.CLOSE
            | ValveEntityFeature.STOP,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "valve#test_mode"
    assert appliance["displayCategories"][0] == "OTHER"
    assert appliance["friendlyName"] == "Test valve mode"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.ModeController",
        "Alexa.EndpointHealth",
        "Alexa.ToggleController",
        "Alexa",
    )

    mode_capability = get_capability(capabilities, "Alexa.ModeController")
    assert mode_capability is not None
    assert mode_capability["instance"] == "valve.state"

    properties = mode_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "mode"} in properties["supported"]

    capability_resources = mode_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "text",
        "value": {"text": "Preset", "locale": "en-US"},
    } in capability_resources["friendlyNames"]

    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Preset"},
    } in capability_resources["friendlyNames"]

    configuration = mode_capability["configuration"]
    assert configuration is not None
    assert configuration["ordered"] is False

    supported_modes = configuration["supportedModes"]
    assert supported_modes is not None
    assert {
        "value": "state.open",
        "modeResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "Open", "locale": "en-US"}},
                {"@type": "asset", "value": {"assetId": "Alexa.Setting.Preset"}},
            ]
        },
    } in supported_modes
    assert {
        "value": "state.closed",
        "modeResources": {
            "friendlyNames": [
                {"@type": "text", "value": {"text": "Closed", "locale": "en-US"}},
                {"@type": "asset", "value": {"assetId": "Alexa.Setting.Preset"}},
            ]
        },
    } in supported_modes

    # Assert for Position Semantics
    position_semantics = mode_capability["semantics"]
    assert position_semantics is not None

    position_action_mappings = position_semantics["actionMappings"]
    assert position_action_mappings is not None
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Close"],
        "directive": {"name": "SetMode", "payload": {"mode": "state.closed"}},
    } in position_action_mappings
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Open"],
        "directive": {"name": "SetMode", "payload": {"mode": "state.open"}},
    } in position_action_mappings

    position_state_mappings = position_semantics["stateMappings"]
    assert position_state_mappings is not None
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Closed"],
        "value": "state.closed",
    } in position_state_mappings
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Open"],
        "value": "state.open",
    } in position_state_mappings

    _, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "valve#test_mode",
        "valve.close_valve",
        hass,
        payload={"mode": "state.closed"},
        instance="valve.state",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "state.closed"

    _, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "valve#test_mode",
        "valve.open_valve",
        hass,
        payload={"mode": "state.open"},
        instance="valve.state",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "state.open"