async def test_thermostat(hass: HomeAssistant) -> None:
    """Test thermostat discovery."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    device = (
        "climate.test_thermostat",
        "cool",
        {
            "temperature": 70.0,
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
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 70.0, "scale": "FAHRENHEIT"},
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

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpoint": {"value": 69.0, "scale": "FAHRENHEIT"}},
    )
    assert call.data["temperature"] == 69.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 69.0, "scale": "FAHRENHEIT"},
    )

    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpoint": {"value": 0.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={
            "targetSetpoint": {"value": 70.0, "scale": "FAHRENHEIT"},
            "lowerSetpoint": {"value": 293.15, "scale": "KELVIN"},
            "upperSetpoint": {"value": 30.0, "scale": "CELSIUS"},
        },
    )
    assert call.data["temperature"] == 70.0
    assert call.data["target_temp_low"] == 68.0
    assert call.data["target_temp_high"] == 86.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 70.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.ThermostatController",
        "lowerSetpoint",
        {"value": 68.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.ThermostatController",
        "upperSetpoint",
        {"value": 86.0, "scale": "FAHRENHEIT"},
    )

    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={
            "lowerSetpoint": {"value": 273.15, "scale": "KELVIN"},
            "upperSetpoint": {"value": 75.0, "scale": "FAHRENHEIT"},
        },
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={
            "lowerSetpoint": {"value": 293.15, "scale": "FAHRENHEIT"},
            "upperSetpoint": {"value": 75.0, "scale": "CELSIUS"},
        },
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": -10.0, "scale": "KELVIN"}},
    )
    assert call.data["temperature"] == 52.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 52.0, "scale": "FAHRENHEIT"},
    )

    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": 20.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    # Setting mode, the payload can be an object with a value attribute...
    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "HEAT"}},
    )
    assert call.data["hvac_mode"] == "heat"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "HEAT")

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "COOL"}},
    )
    assert call.data["hvac_mode"] == "cool"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "COOL")

    # ...it can also be just the mode.
    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": "HEAT"},
    )
    assert call.data["hvac_mode"] == "heat"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "HEAT")

    # Assert we can call custom modes for dry and fan_only
    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "CUSTOM", "customName": "DEHUMIDIFY"}},
    )
    assert call.data["hvac_mode"] == "dry"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "CUSTOM")

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "CUSTOM", "customName": "FAN"}},
    )
    assert call.data["hvac_mode"] == "fan_only"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ThermostatController", "thermostatMode", "CUSTOM")

    # assert unsupported custom mode
    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "CUSTOM", "customName": "INVALID"}},
    )
    assert msg["event"]["payload"]["type"] == "UNSUPPORTED_THERMOSTAT_MODE"

    msg = await assert_request_fails(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": {"value": "INVALID"}},
    )
    assert msg["event"]["payload"]["type"] == "UNSUPPORTED_THERMOSTAT_MODE"

    call, _ = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_hvac_mode",
        hass,
        payload={"thermostatMode": "OFF"},
    )
    assert call.data["hvac_mode"] == "off"

    # Assert we can call presets
    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetThermostatMode",
        "climate#test_thermostat",
        "climate.set_preset_mode",
        hass,
        payload={"thermostatMode": "ECO"},
    )
    assert call.data["preset_mode"] == "eco"