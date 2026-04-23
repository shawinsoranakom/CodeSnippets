async def test_water_heater(hass: HomeAssistant) -> None:
    """Test water_heater discovery."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    device = (
        "water_heater.boyler",
        "gas",
        {
            "temperature": 70.0,
            "target_temp_high": None,
            "target_temp_low": None,
            "current_temperature": 75.0,
            "friendly_name": "Test water heater",
            "supported_features": 1 | 2 | 8,
            "operation_list": ["off", "gas", "eco"],
            "operation_mode": "gas",
            "min_temp": 50,
            "max_temp": 90,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "water_heater#boyler"
    assert appliance["displayCategories"][0] == "WATER_HEATER"
    assert appliance["friendlyName"] == "Test water heater"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.PowerController",
        "Alexa.ThermostatController",
        "Alexa.ModeController",
        "Alexa.TemperatureSensor",
        "Alexa.EndpointHealth",
        "Alexa",
    )

    properties = await reported_properties(hass, "water_heater#boyler")
    properties.assert_equal("Alexa.ModeController", "mode", "operation_mode.gas")
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 70.0, "scale": "FAHRENHEIT"},
    )
    properties.assert_equal(
        "Alexa.TemperatureSensor", "temperature", {"value": 75.0, "scale": "FAHRENHEIT"}
    )

    modes_capability = get_capability(capabilities, "Alexa.ModeController")
    assert modes_capability is not None
    configuration = modes_capability["configuration"]

    supported_modes = ["operation_mode.off", "operation_mode.gas", "operation_mode.eco"]
    for mode in supported_modes:
        assert mode in [item["value"] for item in configuration["supportedModes"]]

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "water_heater#boyler",
        "water_heater.set_temperature",
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
        "water_heater#boyler",
        "water_heater.set_temperature",
        hass,
        payload={"targetSetpoint": {"value": 0.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "water_heater#boyler",
        "water_heater.set_temperature",
        hass,
        payload={
            "targetSetpoint": {"value": 30.0, "scale": "CELSIUS"},
        },
    )
    assert call.data["temperature"] == 86.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 86.0, "scale": "FAHRENHEIT"},
    )

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "AdjustTargetTemperature",
        "water_heater#boyler",
        "water_heater.set_temperature",
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
        "water_heater#boyler",
        "water_heater.set_temperature",
        hass,
        payload={"targetSetpointDelta": {"value": 20.0, "scale": "CELSIUS"}},
    )
    assert msg["event"]["payload"]["type"] == "TEMPERATURE_VALUE_OUT_OF_RANGE"

    # Setting mode, the payload can be an object with a value attribute...
    call, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "water_heater#boyler",
        "water_heater.set_operation_mode",
        hass,
        payload={"mode": "operation_mode.eco"},
        instance="water_heater.operation_mode",
    )
    assert call.data["operation_mode"] == "eco"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ModeController", "mode", "operation_mode.eco")

    call, msg = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "water_heater#boyler",
        "water_heater.set_operation_mode",
        hass,
        payload={"mode": "operation_mode.gas"},
        instance="water_heater.operation_mode",
    )
    assert call.data["operation_mode"] == "gas"
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal("Alexa.ModeController", "mode", "operation_mode.gas")

    # assert unsupported mode
    msg = await assert_request_fails(
        "Alexa.ModeController",
        "SetMode",
        "water_heater#boyler",
        "water_heater.set_operation_mode",
        hass,
        payload={"mode": "operation_mode.invalid"},
        instance="water_heater.operation_mode",
    )
    assert msg["event"]["payload"]["type"] == "INVALID_VALUE"

    call, _ = await assert_request_calls_service(
        "Alexa.ModeController",
        "SetMode",
        "water_heater#boyler",
        "water_heater.set_operation_mode",
        hass,
        payload={"mode": "operation_mode.off"},
        instance="water_heater.operation_mode",
    )
    assert call.data["operation_mode"] == "off"