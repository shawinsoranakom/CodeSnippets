async def async_api_adjust_target_temp(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process an adjust target temperature request for climates and water heaters."""
    data: dict[str, Any]
    entity = directive.entity
    domain = entity.domain
    min_temp = entity.attributes[MIN_MAX_TEMP[domain]["min_temp"]]
    max_temp = entity.attributes[MIN_MAX_TEMP[domain]["max_temp"]]
    unit = hass.config.units.temperature_unit

    temp_delta = temperature_from_object(
        hass, directive.payload["targetSetpointDelta"], interval=True
    )

    response = directive.response()

    current_target_temp_high = entity.attributes.get(climate.ATTR_TARGET_TEMP_HIGH)
    current_target_temp_low = entity.attributes.get(climate.ATTR_TARGET_TEMP_LOW)
    if current_target_temp_high is not None and current_target_temp_low is not None:
        target_temp_high = float(current_target_temp_high) + temp_delta
        if target_temp_high < min_temp or target_temp_high > max_temp:
            raise AlexaTempRangeError(hass, target_temp_high, min_temp, max_temp)

        target_temp_low = float(current_target_temp_low) + temp_delta
        if target_temp_low < min_temp or target_temp_low > max_temp:
            raise AlexaTempRangeError(hass, target_temp_low, min_temp, max_temp)

        data = {
            ATTR_ENTITY_ID: entity.entity_id,
            climate.ATTR_TARGET_TEMP_HIGH: target_temp_high,
            climate.ATTR_TARGET_TEMP_LOW: target_temp_low,
        }

        response.add_context_property(
            {
                "name": "upperSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": target_temp_high, "scale": API_TEMP_UNITS[unit]},
            }
        )
        response.add_context_property(
            {
                "name": "lowerSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": target_temp_low, "scale": API_TEMP_UNITS[unit]},
            }
        )
    else:
        current_target_temp: str | None = entity.attributes.get(ATTR_TEMPERATURE)
        if current_target_temp is None:
            raise AlexaUnsupportedThermostatTargetStateError(
                "The current target temperature is not set, "
                "cannot adjust target temperature"
            )
        target_temp = float(current_target_temp) + temp_delta

        if target_temp < min_temp or target_temp > max_temp:
            raise AlexaTempRangeError(hass, target_temp, min_temp, max_temp)

        data = {ATTR_ENTITY_ID: entity.entity_id, ATTR_TEMPERATURE: target_temp}
        response.add_context_property(
            {
                "name": "targetSetpoint",
                "namespace": "Alexa.ThermostatController",
                "value": {"value": target_temp, "scale": API_TEMP_UNITS[unit]},
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