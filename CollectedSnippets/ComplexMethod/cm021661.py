async def test_thermostat_dual(hass: HomeAssistant) -> None:
    """Test thermostat discovery with auto mode, with upper and lower target temperatures."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    device = (
        "climate.test_thermostat",
        "auto",
        {
            "temperature": None,
            "target_temp_high": 80.0,
            "target_temp_low": 60.0,
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

    assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ThermostatController",
        "Alexa.TemperatureSensor",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    properties = await reported_properties(hass, "climate#test_thermostat")
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "AUTO")
    properties.assert_equal(
        "Alexa.ThermostatController",
        "upperSetpoint",
        {"value": 80.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.ThermostatController",
        "lowerSetpoint",
        {"value": 60.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.TemperatureSensor", "temperature", {"value": 75.0, "scale": "FAHRENHEIT"}
    )

    # Adjust temperature when in auto mode
    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": -5.0, "scale": "KELVIN"}},
    )
    assert call.data["target_temp_high"] == 71.0
    assert call.data["target_temp_low"] == 51.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "upperSetpoint",
        {"value": 71.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.ThermostatController",
        "lowerSetpoint",
        {"value": 51.0, "scale": "FAHRENHEIT"},
    )

    # Fails if the upper setpoint goes too high
    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": 6.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    # Fails if the lower setpoint goes too low
    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": -6.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"