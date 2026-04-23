async def test_onoff_thermostat(hass: HomeAssistant) -> None:
    """Test onoff thermostat discovery."""
    on_off_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    hass.config.units = METRIC_SYSTEM
    device = (
        "climate.test_thermostat",
        "cool",
        {
            "temperature": 20.0,
            "target_temp_high": None,
            "target_temp_low": None,
            "current_temperature": 19.0,
            "friendly_name": "Test Thermostat",
            "supported_features": on_off_features,
            "hvac_modes": ["auto"],
            "min_temp": 7,
            "max_temp": 30,
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
        {"value": 20.0, "scale": "CELSIUS"},
    )
    properties.assert_equal(
        "Alexa.TemperatureSensor", "temperature", {"value": 19.0, "scale": "CELSIUS"}
    )

    thermostat_capability = get_capability(capabilities, "Alexa.ThermostatController")
    assert thermostat_capability is not None
    configuration = thermostat_capability["configuration"]
    assert configuration["supportsScheduling"] is False

    supported_modes = ["AUTO"]
    for mode in supported_modes:
        assert mode in configuration["supportedModes"]

    call, msg = await assert_request_calls_service(
        "Alexa.ThermostatController",
        "SetTargetTemperature",
        "climate#test_thermostat",
        "climate.set_temperature",
        hass,
        payload={"targetSetpoint": {"value": 21.0, "scale": "CELSIUS"}},
    )
    assert call.data["temperature"] == 21.0
    properties = ReportedProperties(msg["context"]["properties"])
    properties.assert_equal(
        "Alexa.ThermostatController",
        "targetSetpoint",
        {"value": 21.0, "scale": "CELSIUS"},
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

    await assert_request_calls_service(
        "Alexa.PowerController",
        "TurnOn",
        "climate#test_thermostat",
        "climate.turn_on",
        hass,
    )
    await assert_request_calls_service(
        "Alexa.PowerController",
        "TurnOff",
        "climate#test_thermostat",
        "climate.turn_off",
        hass,
    )

    # Test the power controller is not enabled when there is no `off` mode
    device = (
        "climate.test_thermostat",
        "cool",
        {
            "temperature": 20.0,
            "target_temp_high": None,
            "target_temp_low": None,
            "current_temperature": 19.0,
            "friendly_name": "Test Thermostat",
            "supported_features": ClimateEntityFeature.TARGET_TEMPERATURE,
            "hvac_modes": ["auto"],
            "min_temp": 7,
            "max_temp": 30,
        },
    )
    appliance = await discovery_test(device, hass)

    assert appliance["endpointId"] == "climate#test_thermostat"
    assert appliance["displayCategories"][0] == "THERMOSTAT"
    assert appliance["friendlyName"] == "Test Thermostat"

    capabilities = assert_endpoint_capabilities(
        appliance,
        "Alexa.ThermostatController",
        "Alexa.TemperatureSensor",
        "Alexa.EndpointHealth",
        "Alexa",
    )