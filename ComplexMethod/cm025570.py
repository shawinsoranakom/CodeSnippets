async def async_service_set_program_and_options(call: ServiceCall) -> None:
    """Service for setting a program and options."""
    data = dict(call.data)
    program = data.pop(ATTR_PROGRAM, None)
    affects_to = data.pop(ATTR_AFFECTS_TO)
    client, ha_id = await _get_client_and_ha_id(call.hass, data.pop(ATTR_DEVICE_ID))

    options: list[Option] = []

    for option, value in data.items():
        if option in PROGRAM_ENUM_OPTIONS:
            options.append(
                Option(
                    PROGRAM_ENUM_OPTIONS[option][0],
                    PROGRAM_ENUM_OPTIONS[option][1][value],
                )
            )
        elif option in PROGRAM_OPTIONS:
            option_key = PROGRAM_OPTIONS[option][0]
            options.append(Option(option_key, value))

    method_call: Awaitable[Any]
    exception_translation_key: str
    if program:
        program = (
            program
            if isinstance(program, ProgramKey)
            else TRANSLATION_KEYS_PROGRAMS_MAP[program]
        )

        if affects_to == AFFECTS_TO_ACTIVE_PROGRAM:
            method_call = client.start_program(
                ha_id, program_key=program, options=options
            )
            exception_translation_key = "start_program"
        elif affects_to == AFFECTS_TO_SELECTED_PROGRAM:
            method_call = client.set_selected_program(
                ha_id, program_key=program, options=options
            )
            exception_translation_key = "select_program"
    else:
        array_of_options = ArrayOfOptions(options)
        if affects_to == AFFECTS_TO_ACTIVE_PROGRAM:
            method_call = client.set_active_program_options(
                ha_id, array_of_options=array_of_options
            )
            exception_translation_key = "set_options_active_program"
        else:
            # affects_to is AFFECTS_TO_SELECTED_PROGRAM
            method_call = client.set_selected_program_options(
                ha_id, array_of_options=array_of_options
            )
            exception_translation_key = "set_options_selected_program"

    try:
        await method_call
    except HomeConnectError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key=exception_translation_key,
            translation_placeholders={
                **get_dict_from_home_connect_error(err),
                **({"program": program} if program else {}),
            },
        ) from err