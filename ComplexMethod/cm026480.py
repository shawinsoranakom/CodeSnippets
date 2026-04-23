async def async_api_set_range(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a next request."""
    entity = directive.entity
    instance = directive.instance
    domain = entity.domain
    service = None
    data: dict[str, Any] = {ATTR_ENTITY_ID: entity.entity_id}
    range_value = directive.payload["rangeValue"]
    supported = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

    # Cover Position
    if instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
        range_value = int(range_value)
        if supported & cover.CoverEntityFeature.CLOSE and range_value == 0:
            service = cover.SERVICE_CLOSE_COVER
        elif supported & cover.CoverEntityFeature.OPEN and range_value == 100:
            service = cover.SERVICE_OPEN_COVER
        else:
            service = cover.SERVICE_SET_COVER_POSITION
            data[cover.ATTR_POSITION] = range_value

    # Cover Tilt
    elif instance == f"{cover.DOMAIN}.tilt":
        range_value = int(range_value)
        if supported & cover.CoverEntityFeature.CLOSE_TILT and range_value == 0:
            service = cover.SERVICE_CLOSE_COVER_TILT
        elif supported & cover.CoverEntityFeature.OPEN_TILT and range_value == 100:
            service = cover.SERVICE_OPEN_COVER_TILT
        else:
            service = cover.SERVICE_SET_COVER_TILT_POSITION
            data[cover.ATTR_TILT_POSITION] = range_value

    # Fan Speed
    elif instance == f"{fan.DOMAIN}.{fan.ATTR_PERCENTAGE}":
        range_value = int(range_value)
        if range_value == 0:
            service = fan.SERVICE_TURN_OFF
        elif supported & fan.FanEntityFeature.SET_SPEED:
            service = fan.SERVICE_SET_PERCENTAGE
            data[fan.ATTR_PERCENTAGE] = range_value
        else:
            service = fan.SERVICE_TURN_ON

    # Humidifier target humidity
    elif instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_HUMIDITY}":
        range_value = int(range_value)
        service = humidifier.SERVICE_SET_HUMIDITY
        data[humidifier.ATTR_HUMIDITY] = range_value

    # Input Number Value
    elif instance == f"{input_number.DOMAIN}.{input_number.ATTR_VALUE}":
        range_value = float(range_value)
        service = input_number.SERVICE_SET_VALUE
        min_value = float(entity.attributes[input_number.ATTR_MIN])
        max_value = float(entity.attributes[input_number.ATTR_MAX])
        data[input_number.ATTR_VALUE] = min(max_value, max(min_value, range_value))

    # Input Number Value
    elif instance == f"{number.DOMAIN}.{number.ATTR_VALUE}":
        range_value = float(range_value)
        service = number.SERVICE_SET_VALUE
        min_value = float(entity.attributes[number.ATTR_MIN])
        max_value = float(entity.attributes[number.ATTR_MAX])
        data[number.ATTR_VALUE] = min(max_value, max(min_value, range_value))

    # Vacuum Fan Speed
    elif instance == f"{vacuum.DOMAIN}.{vacuum.ATTR_FAN_SPEED}":
        service = vacuum.SERVICE_SET_FAN_SPEED
        speed_list = entity.attributes[vacuum.ATTR_FAN_SPEED_LIST]
        speed = next(
            (v for i, v in enumerate(speed_list) if i == int(range_value)), None
        )

        if not speed:
            msg = "Entity does not support value"
            raise AlexaInvalidValueError(msg)

        data[vacuum.ATTR_FAN_SPEED] = speed

    # Valve Position
    elif instance == f"{valve.DOMAIN}.{valve.ATTR_POSITION}":
        range_value = int(range_value)
        if supported & valve.ValveEntityFeature.CLOSE and range_value == 0:
            service = valve.SERVICE_CLOSE_VALVE
        elif supported & valve.ValveEntityFeature.OPEN and range_value == 100:
            service = valve.SERVICE_OPEN_VALVE
        else:
            service = valve.SERVICE_SET_VALVE_POSITION
            data[valve.ATTR_POSITION] = range_value

    else:
        raise AlexaInvalidDirectiveError(DIRECTIVE_NOT_SUPPORTED)

    await hass.services.async_call(
        domain, service, data, blocking=False, context=context
    )

    response = directive.response()
    response.add_context_property(
        {
            "namespace": "Alexa.RangeController",
            "instance": instance,
            "name": "rangeValue",
            "value": range_value,
        }
    )

    return response