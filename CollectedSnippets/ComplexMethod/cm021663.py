async def test_alarm_control_panel_disarmed(hass: HomeAssistant) -> None:
    """Test alarm_control_panel discovery."""
    device = (
        "alarm_control_panel.test_1",
        "disarmed",
        {
            "friendly_name": "Test Alarm Control Panel 1",
            "code_arm_required": False,
            "code_format": "number",
            "code": "1234",
            "supported_features": 31,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "alarm_control_panel#test_1"
    assert appliance["displayCategories"][0] == "SECURITY_PANEL"
    assert appliance["friendlyName"] == "Test Alarm Control Panel 1"
    capabilities = assert_endpoint_capabilities(
        appliance, "Alexa.SecurityPanelController", "Alexa.EndpointHealth", "Alexa"
    )
    security_panel_capability = get_capability(
        capabilities, "Alexa.SecurityPanelController"
    )
    assert security_panel_capability is not None
    configuration = security_panel_capability["configuration"]
    assert {"type": "FOUR_DIGIT_PIN"} in configuration["supportedAuthorizationTypes"]
    assert {"value": "DISARMED"} in configuration["supportedArmStates"]
    assert {"value": "ARMED_STAY"} in configuration["supportedArmStates"]
    assert {"value": "ARMED_AWAY"} in configuration["supportedArmStates"]
    assert {"value": "ARMED_NIGHT"} in configuration["supportedArmStates"]

    properties = await reported_properties(hass, "alarm_control_panel#test_1")
    properties.assert_equal("Alexa.SecurityPanelController", "armState", "DISARMED")

    _, msg = await assert_request_calls_service(
        "Alexa.SecurityPanelController",
        "Arm",
        "alarm_control_panel#test_1",
        "alarm_control_panel.alarm_arm_home",
        hass,
        response_type="Arm.Response",
        payload={"armState": "ARMED_STAY"},
    )
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.SecurityPanelController", "armState", "ARMED_STAY")

    _, msg = await assert_request_calls_service(
        "Alexa.SecurityPanelController",
        "Arm",
        "alarm_control_panel#test_1",
        "alarm_control_panel.alarm_arm_away",
        hass,
        response_type="Arm.Response",
        payload={"armState": "ARMED_AWAY"},
    )
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.SecurityPanelController", "armState", "ARMED_AWAY")

    _, msg = await assert_request_calls_service(
        "Alexa.SecurityPanelController",
        "Arm",
        "alarm_control_panel#test_1",
        "alarm_control_panel.alarm_arm_night",
        hass,
        response_type="Arm.Response",
        payload={"armState": "ARMED_NIGHT"},
    )
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.SecurityPanelController", "armState", "ARMED_NIGHT")