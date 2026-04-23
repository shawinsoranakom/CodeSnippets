async def test_no_current_target_temp_adjusting_temp(hass: HomeAssistant) -> None:
    """Test thermostat adjusting temp with no initial target temperature."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    device = (
        "climate.test_thermostat",
        "cool",
        {
            "temperature": None,
            "target_temp_high": None,
            "target_temp_low": None,
            "current_temperature": 75.0,
            "friendly_name": "Test Thermostat",
            "supported_features": 1 | 2 | 4 | 128,
            "hvac_modes": ["off", "heat", "cool", "auto", "dry", "fan_only"],
            "preset_mode": None,
            "preset_modes": ["eco"],
            "min_temp": 50,
            "max_temp": 90,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "climate#test_thermostat"
    assert appliance["displayCategories"][0] == "THERMOSTAT"
    assert appliance["friendlyName"] == "Test Thermostat"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ThermostatController",
        "Alexa.TemperatureSensor",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    properties = await reported_properties(hass, "climate#test_thermostat")
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "COOL")
    properties.assert_not_has_property(
        "Alexa.ThermostatController",
        "targetSetpoint",
    )
    properties.assert_equal(
        "Alexa.TemperatureSensor", "temperature", {"value": 75.0, "scale": "FAHRENHEIT"}
    )

    thermostat_capability = get_capability(capabilities, "Alexa.ThermostatController")
    assert thermostat_capability is not None
    configuration = thermostat_capability["configuration"]
    assert configuration["supportsScheduling"] is False

    supported_modes = ["OFF", "HEAT", "COOL", "AUTO", "ECO", "CUSTOM"]
    for mode in supported_modes:
        assert mode in configuration["supportedModes"]

    # Adjust temperature where target temp is not set
    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": -5.0, "scale": "KELVIN"}},
    )
    assert msg["event"]["payload"]["type"] == "INVALID_TARGET_STATE"
    assert msg["event"]["payload"]["message"] == (
        "The current target temperature is not set, cannot adjust target temperature"
    )