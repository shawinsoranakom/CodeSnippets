async def async_handle_message(
    hass: HomeAssistant,
    config: AbstractConfig,
    request: dict[str, Any],
    context: Context | None = None,
    enabled: bool = True,
) -> dict[str, Any]:
    """Handle incoming API messages.

    If enabled is False, the response to all messages will be a
    BRIDGE_UNREACHABLE error. This can be used if the API has been disabled in
    configuration.
    """
    assert request[API_DIRECTIVE][API_HEADER]["payloadVersion"] == "3"

    if context is None:
        context = Context()

    directive = AlexaDirective(request)

    try:
        if not enabled:
            raise AlexaBridgeUnreachableError(  # noqa: TRY301
                "Alexa API not enabled in Home Assistant configuration"
            )

        await config.set_authorized(True)

        if directive.has_endpoint:
            directive.load_entity(hass, config)

        funct_ref = HANDLERS.get((directive.namespace, directive.name))
        if funct_ref:
            response = await funct_ref(hass, config, directive, context)
            if directive.has_endpoint:
                response.merge_context_properties(directive.endpoint)
        else:
            _LOGGER.warning(
                "Unsupported API request %s/%s", directive.namespace, directive.name
            )
            response = directive.error()
    except AlexaError as err:
        response = directive.error(
            error_type=str(err.error_type),
            error_message=err.error_message,
            payload=err.payload,
        )
    except Exception:
        _LOGGER.exception(
            "Uncaught exception processing Alexa %s/%s request (%s)",
            directive.namespace,
            directive.name,
            directive.entity_id or "-",
        )
        response = directive.error(error_message="Unknown error")

    request_info: dict[str, Any] = {
        "namespace": directive.namespace,
        "name": directive.name,
    }

    if directive.has_endpoint:
        assert directive.entity_id is not None
        request_info["entity_id"] = directive.entity_id

    hass.bus.async_fire(
        EVENT_ALEXA_SMART_HOME,
        {
            "request": request_info,
            "response": {"namespace": response.namespace, "name": response.name},
        },
        context=context,
    )

    return response.serialize()