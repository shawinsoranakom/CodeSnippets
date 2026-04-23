async def async_api_set_mode(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a SetMode directive."""
    entity = directive.entity
    instance = directive.instance
    domain = entity.domain
    service = None
    data: dict[str, Any] = {ATTR_ENTITY_ID: entity.entity_id}
    mode = directive.payload["mode"]

    # Fan Direction
    if instance == f"{fan.DOMAIN}.{fan.ATTR_DIRECTION}":
        direction = mode.split(".")[1]
        if direction in (fan.DIRECTION_REVERSE, fan.DIRECTION_FORWARD):
            service = fan.SERVICE_SET_DIRECTION
            data[fan.ATTR_DIRECTION] = direction

    # Fan preset_mode
    elif instance == f"{fan.DOMAIN}.{fan.ATTR_PRESET_MODE}":
        preset_mode = mode.split(".")[1]
        preset_modes: list[str] | None = entity.attributes.get(fan.ATTR_PRESET_MODES)
        if (
            preset_mode != PRESET_MODE_NA
            and preset_modes
            and preset_mode in preset_modes
        ):
            service = fan.SERVICE_SET_PRESET_MODE
            data[fan.ATTR_PRESET_MODE] = preset_mode
        else:
            msg = f"Entity '{entity.entity_id}' does not support Preset '{preset_mode}'"
            raise AlexaInvalidValueError(msg)

    # Humidifier mode
    elif instance == f"{humidifier.DOMAIN}.{humidifier.ATTR_MODE}":
        mode = mode.split(".")[1]
        modes: list[str] | None = entity.attributes.get(humidifier.ATTR_AVAILABLE_MODES)
        if mode != PRESET_MODE_NA and modes and mode in modes:
            service = humidifier.SERVICE_SET_MODE
            data[humidifier.ATTR_MODE] = mode
        else:
            msg = f"Entity '{entity.entity_id}' does not support Mode '{mode}'"
            raise AlexaInvalidValueError(msg)

    # Remote Activity
    elif instance == f"{remote.DOMAIN}.{remote.ATTR_ACTIVITY}":
        activity = mode.split(".")[1]
        activities: list[str] | None = entity.attributes.get(remote.ATTR_ACTIVITY_LIST)
        if activity != PRESET_MODE_NA and activities and activity in activities:
            service = remote.SERVICE_TURN_ON
            data[remote.ATTR_ACTIVITY] = activity
        else:
            msg = f"Entity '{entity.entity_id}' does not support Mode '{mode}'"
            raise AlexaInvalidValueError(msg)

    # Water heater operation mode
    elif instance == f"{water_heater.DOMAIN}.{water_heater.ATTR_OPERATION_MODE}":
        operation_mode = mode.split(".")[1]
        operation_modes: list[str] | None = entity.attributes.get(
            water_heater.ATTR_OPERATION_LIST
        )
        if (
            operation_mode != PRESET_MODE_NA
            and operation_modes
            and operation_mode in operation_modes
        ):
            service = water_heater.SERVICE_SET_OPERATION_MODE
            data[water_heater.ATTR_OPERATION_MODE] = operation_mode
        else:
            msg = f"Entity '{entity.entity_id}' does not support Operation mode '{operation_mode}'"
            raise AlexaInvalidValueError(msg)

    # Cover Position
    elif instance == f"{cover.DOMAIN}.{cover.ATTR_POSITION}":
        position = mode.split(".")[1]

        if position == cover.CoverState.CLOSED:
            service = cover.SERVICE_CLOSE_COVER
        elif position == cover.CoverState.OPEN:
            service = cover.SERVICE_OPEN_COVER
        elif position == "custom":
            service = cover.SERVICE_STOP_COVER

    # Valve position state
    elif instance == f"{valve.DOMAIN}.state":
        position = mode.split(".")[1]

        if position == valve.STATE_CLOSED:
            service = valve.SERVICE_CLOSE_VALVE
        elif position == valve.STATE_OPEN:
            service = valve.SERVICE_OPEN_VALVE

    if not service:
        raise AlexaInvalidDirectiveError(DIRECTIVE_NOT_SUPPORTED)

    await hass.services.async_call(
        domain, service, data, blocking=False, context=context
    )

    response = directive.response()
    response.add_context_property(
        {
            "namespace": "Alexa.ModeController",
            "instance": instance,
            "name": "mode",
            "value": mode,
        }
    )

    return response