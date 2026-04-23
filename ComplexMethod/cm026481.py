async def async_api_adjust_range(
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
    range_delta = directive.payload["rangeValueDelta"]
    range_delta_default = bool(directive.payload["rangeValueDeltaDefault"])
    response_value: float | None = 0

    # Cover Position
    if instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
        range_delta = int(range_delta * 20) if range_delta_default else int(range_delta)
        service = SERVICE_SET_COVER_POSITION
        if not (current := entity.attributes.get(cover.ATTR_CURRENT_POSITION)):
            msg = f"Unable to determine {entity.entity_id} current position"
            raise AlexaInvalidValueError(msg)
        position = response_value = min(100, max(0, range_delta + current))
        if position == 100:
            service = cover.SERVICE_OPEN_COVER
        elif position == 0:
            service = cover.SERVICE_CLOSE_COVER
        else:
            data[cover.ATTR_POSITION] = position

    # Cover Tilt
    elif instance == f"{cover.DOMAIN}.tilt":
        range_delta = int(range_delta * 20) if range_delta_default else int(range_delta)
        service = SERVICE_SET_COVER_TILT_POSITION
        current = entity.attributes.get(cover.ATTR_TILT_POSITION)
        if not current:
            msg = f"Unable to determine {entity.entity_id} current tilt position"
            raise AlexaInvalidValueError(msg)
        tilt_position = response_value = min(100, max(0, range_delta + current))
        if tilt_position == 100:
            service = cover.SERVICE_OPEN_COVER_TILT
        elif tilt_position == 0:
            service = cover.SERVICE_CLOSE_COVER_TILT
        else:
            data[cover.ATTR_TILT_POSITION] = tilt_position

    # Fan speed percentage
    elif instance == f"{fan.DOMAIN}.{fan.ATTR_PERCENTAGE}":
        percentage_step = entity.attributes.get(fan.ATTR_PERCENTAGE_STEP) or 20
        range_delta = (
            int(range_delta * percentage_step)
            if range_delta_default
            else int(range_delta)
        )
        service = fan.SERVICE_SET_PERCENTAGE
        if not (current := entity.attributes.get(fan.ATTR_PERCENTAGE)):
            msg = f"Unable to determine {entity.entity_id} current fan speed"
            raise AlexaInvalidValueError(msg)
        percentage = response_value = min(100, max(0, range_delta + current))
        if percentage:
            data[fan.ATTR_PERCENTAGE] = percentage
        else:
            service = fan.SERVICE_TURN_OFF

    # Humidifier target humidity
    elif instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_HUMIDITY}":
        percentage_step = 5
        range_delta = (
            int(range_delta * percentage_step)
            if range_delta_default
            else int(range_delta)
        )
        service = humidifier.SERVICE_SET_HUMIDITY
        if not (current := entity.attributes.get(humidifier.ATTR_HUMIDITY)):
            msg = f"Unable to determine {entity.entity_id} current target humidity"
            raise AlexaInvalidValueError(msg)
        min_value = entity.attributes.get(humidifier.ATTR_MIN_HUMIDITY, 10)
        max_value = entity.attributes.get(humidifier.ATTR_MAX_HUMIDITY, 90)
        percentage = response_value = min(
            max_value, max(min_value, range_delta + current)
        )
        if percentage:
            data[humidifier.ATTR_HUMIDITY] = percentage

    # Input Number Value
    elif instance == f"{input_number.DOMAIN}.{input_number.ATTR_VALUE}":
        range_delta = float(range_delta)
        service = input_number.SERVICE_SET_VALUE
        min_value = float(entity.attributes[input_number.ATTR_MIN])
        max_value = float(entity.attributes[input_number.ATTR_MAX])
        current = float(entity.state)
        data[input_number.ATTR_VALUE] = response_value = min(
            max_value, max(min_value, range_delta + current)
        )

    # Number Value
    elif instance == f"{number.DOMAIN}.{number.ATTR_VALUE}":
        range_delta = float(range_delta)
        service = number.SERVICE_SET_VALUE
        min_value = float(entity.attributes[number.ATTR_MIN])
        max_value = float(entity.attributes[number.ATTR_MAX])
        current = float(entity.state)
        data[number.ATTR_VALUE] = response_value = min(
            max_value, max(min_value, range_delta + current)
        )

    # Vacuum Fan Speed
    elif instance == f"{vacuum.DOMAIN}.{vacuum.ATTR_FAN_SPEED}":
        range_delta = int(range_delta)
        service = vacuum.SERVICE_SET_FAN_SPEED
        speed_list = entity.attributes[vacuum.ATTR_FAN_SPEED_LIST]
        current_speed = entity.attributes[vacuum.ATTR_FAN_SPEED]
        current_speed_index = next(
            (i for i, v in enumerate(speed_list) if v == current_speed), 0
        )
        new_speed_index = min(
            len(speed_list) - 1, max(0, current_speed_index + range_delta)
        )
        speed = next(
            (v for i, v in enumerate(speed_list) if i == new_speed_index), None
        )
        data[vacuum.ATTR_FAN_SPEED] = response_value = speed

    # Valve Position
    elif instance == f"{valve.DOMAIN}.{valve.ATTR_POSITION}":
        range_delta = int(range_delta * 20) if range_delta_default else int(range_delta)
        service = valve.SERVICE_SET_VALVE_POSITION
        if not (current := entity.attributes.get(valve.ATTR_POSITION)):
            msg = f"Unable to determine {entity.entity_id} current position"
            raise AlexaInvalidValueError(msg)
        position = response_value = min(100, max(0, range_delta + current))
        if position == 100:
            service = valve.SERVICE_OPEN_VALVE
        elif position == 0:
            service = valve.SERVICE_CLOSE_VALVE
        else:
            data[valve.ATTR_POSITION] = position

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
            "value": response_value,
        }
    )

    return response