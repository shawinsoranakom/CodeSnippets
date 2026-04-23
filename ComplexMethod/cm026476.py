async def async_api_set_target_temp(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a set target temperature request."""
    entity = directive.entity
    domain = entity.domain

    min_temp = entity.attributes[MIN_MAX_TEMP[domain]["min_temp"]]
    max_temp = entity.attributes["max_temp"]
    unit = hass.config.units.temperature_unit

    data: dict[str, Any] = {ATTR_ENTITY_ID: entity.entity_id}

    payload = directive.payload
    response = directive.response()
    if "targetSetpoint" in payload:
        temp = temperature_from_object(hass, payload["targetSetpoint"])
        if temp < min_temp or temp > max_temp:
            raise AlexaTempRangeError(hass, temp, min_temp, max_temp)
        data[ATTR_TEMPERATURE] = temp
        response.add_context_property(
            {
                "name": "targetSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": temp, "scale": API_TEMP_UNITS[unit]},
            }
        )
    if "lowerSetpoint" in payload:
        temp_low = temperature_from_object(hass, payload["lowerSetpoint"])
        if temp_low < min_temp or temp_low > max_temp:
            raise AlexaTempRangeError(hass, temp_low, min_temp, max_temp)
        data[climate.ATTR_TARGET_TEMP_LOW] = temp_low
        response.add_context_property(
            {
                "name": "lowerSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": temp_low, "scale": API_TEMP_UNITS[unit]},
            }
        )
    if "upperSetpoint" in payload:
        temp_high = temperature_from_object(hass, payload["upperSetpoint"])
        if temp_high < min_temp or temp_high > max_temp:
            raise AlexaTempRangeError(hass, temp_high, min_temp, max_temp)
        data[climate.ATTR_TARGET_TEMP_HIGH] = temp_high
        response.add_context_property(
            {
                "name": "upperSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": temp_high, "scale": API_TEMP_UNITS[unit]},
            }
        )

    service = SERVICE_SET_TEMPERATURE[domain]

    await hass.services.async_call(
        entity.domain,
        service,
        data,
        blocking=False,
        context=context,
    )

    return response