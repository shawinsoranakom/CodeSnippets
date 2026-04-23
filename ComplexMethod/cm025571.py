async def async_service_start_selected_program(call: ServiceCall) -> None:
    """Service to start a program that is already selected."""
    data = dict(call.data)
    client, ha_id = await _get_client_and_ha_id(call.hass, data.pop(ATTR_DEVICE_ID))
    try:
        try:
            program_obj = await client.get_active_program(ha_id)
        except NoProgramActiveError:
            program_obj = await client.get_selected_program(ha_id)
    except HomeConnectError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="fetch_program_error",
            translation_placeholders=get_dict_from_home_connect_error(err),
        ) from err
    if not program_obj.key:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="no_program_to_start",
        )

    program = program_obj.key
    options_dict = {option.key: option for option in program_obj.options or []}
    for option, value in data.items():
        option_key = PROGRAM_OPTIONS[option][0]
        options_dict[option_key] = Option(option_key, value)

    try:
        await client.start_program(
            ha_id,
            program_key=program,
            options=list(options_dict.values()) if options_dict else None,
        )
    except HomeConnectError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="start_program",
            translation_placeholders={
                "program": program,
                **get_dict_from_home_connect_error(err),
            },
        ) from err