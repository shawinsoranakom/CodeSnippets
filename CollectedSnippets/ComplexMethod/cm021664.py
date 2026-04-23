async def test_cover_position_mode(hass: HomeAssistant) -> None:
    """Test cover discovery and position using modeController."""
    device = (
        "cover.test_mode",
        "open",
        {
            "friendly_name": "Test cover mode",
            "device_class": "blind",
            "supported_features": 3,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "cover#test_mode"
    assert appliance["displayCategories"][0] == "INTERIOR_BLIND"
    assert appliance["friendlyName"] == "Test cover mode"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ModeController",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    mode_capability = get_capability(capabilities, "Alexa.ModeController")
    assert mode_capability is not None
    assert mode_capability["instance"] == "cover.position"

    properties = mode_capability["properties"]
    assert properties["nonControllable"] is False
    assert {"name": "mode"} in properties["supported"]

    capability_resources = mode_capability["capabilityResources"]
    assert capability_resources is not None
    assert {
        "@type": "text",
        "value": {"text": "Position", "locale": "en-US"},
    } in capability_resources["friendlyNames"]

    assert {
        "@type": "asset",
        "value": {"assetId": "Alexa.Setting.Opening"},
    } in capability_resources["friendlyNames"]

    configuration = mode_capability["configuration"]
    assert configuration is not None
    assert configuration["ordered"] is False

    supported_modes = configuration["supportedModes"]
    assert supported_modes is not None
    assert {
        "value": "position.open",
        "modeResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Open"}}
            ]
        },
    } in supported_modes
    assert {
        "value": "position.closed",
        "modeResources": {
            "friendlyNames": [
                {"@type": "asset", "value": {"assetId": "Alexa.Value.Close"}}
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
        "actions": ["Alexa.Actions.Lower", "Alexa.Actions.Close"],
        "directive": {"name": "SetMode", "payload": {"mode": "position.closed"}},
    } in position_action_mappings
    assert {
        "@type": "ActionsToDirective",
        "actions": ["Alexa.Actions.Raise", "Alexa.Actions.Open"],
        "directive": {"name": "SetMode", "payload": {"mode": "position.open"}},
    } in position_action_mappings

    position_state_mappings = position_semantics["stateMappings"]
    assert position_state_mappings is not None
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Closed"],
        "value": "position.closed",
    } in position_state_mappings
    assert {
        "@type": "StatesToValue",
        "states": ["Alexa.States.Open"],
        "value": "position.open",
    } in position_state_mappings

    _, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "cover#test_mode",
        "cover.close_cover",
        hass,
        payload={"mode": "position.closed"},
        instance="cover.position",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "position.closed"

    _, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "cover#test_mode",
        "cover.open_cover",
        hass,
        payload={"mode": "position.open"},
        instance="cover.position",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "position.open"

    _, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "cover#test_mode",
        "cover.stop_cover",
        hass,
        payload={"mode": "position.custom"},
        instance="cover.position",
    )
    properties = msg["context"]["properties"][0]
    assert properties["name"] == "mode"
    assert properties["namespace"] == "Alexa.ModeController"
    assert properties["value"] == "position.custom"