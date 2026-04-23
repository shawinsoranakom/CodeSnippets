async def async_api_set_thermostat_mode(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a set thermostat mode request."""
    operation_list: list[str]

    entity = directive.entity
    mode = directive.payload["thermostatMode"]
    mode = mode if isinstance(mode, str) else mode["value"]

    data: dict[str, Any] = {ATTR_ENTITY_ID: entity.entity_id}

    ha_preset = next((k for k, v in API_THERMOSTAT_PRESETS.items() if v == mode), None)

    if ha_preset:
        presets = entity.attributes.get(climate.ATTR_PRESET_MODES) or []

        if ha_preset not in presets:
            msg = f"The requested thermostat mode {ha_preset} is not supported"
            raise AlexaUnsupportedThermostatModeError(msg)

        service = climate.SERVICE_SET_PRESET_MODE
        data[climate.ATTR_PRESET_MODE] = ha_preset

    elif mode == "CUSTOM":
        operation_list = entity.attributes.get(climate.ATTR_HVAC_MODES) or []
        custom_mode = directive.payload["thermostatMode"]["customName"]
        custom_mode = next(
            (k for k, v in API_THERMOSTAT_MODES_CUSTOM.items() if v == custom_mode),
            None,
        )
        if custom_mode not in operation_list:
            msg = (
                f"The requested thermostat mode {mode}: {custom_mode} is not supported"
            )
            raise AlexaUnsupportedThermostatModeError(msg)

        service = climate.SERVICE_SET_HVAC_MODE
        data[climate.ATTR_HVAC_MODE] = custom_mode

    else:
        operation_list = entity.attributes.get(climate.ATTR_HVAC_MODES) or []
        ha_modes: dict[str, str] = {
            k: v for k, v in API_THERMOSTAT_MODES.items() if v == mode
        }
        ha_mode: str | None = next(
            iter(set(ha_modes).intersection(operation_list)), None
        )
        if ha_mode not in operation_list:
            msg = f"The requested thermostat mode {mode} is not supported"
            raise AlexaUnsupportedThermostatModeError(msg)

        service = climate.SERVICE_SET_HVAC_MODE
        data[climate.ATTR_HVAC_MODE] = ha_mode

    response = directive.response()
    await hass.services.async_call(
        climate.DOMAIN, service, data, blocking=False, context=context
    )
    response.add_context_property(
        {
            "name": "thermostatMode",
            "namespace": "Alexa.ThermostatController",
            "value": mode,
        }
    )

    return response