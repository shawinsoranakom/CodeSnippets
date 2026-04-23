async def async_api_select_input(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a set input request."""
    media_input = directive.payload["input"]
    entity = directive.entity

    # Attempt to map the ALL UPPERCASE payload name to a source.
    # Strips trailing 1 to match single input devices.
    source_list = entity.attributes.get(media_player.ATTR_INPUT_SOURCE_LIST) or []
    for source in source_list:
        formatted_source = (
            source.lower().replace("-", "").replace("_", "").replace(" ", "")
        )
        media_input = media_input.lower().replace(" ", "")
        if (
            formatted_source in Inputs.VALID_SOURCE_NAME_MAP
            and formatted_source == media_input
        ) or (
            media_input.endswith("1") and formatted_source == media_input.rstrip("1")
        ):
            media_input = source
            break
    else:
        msg = (
            f"failed to map input {media_input} to a media source on {entity.entity_id}"
        )
        raise AlexaInvalidValueError(msg)

    data: dict[str, Any] = {
        ATTR_ENTITY_ID: entity.entity_id,
        media_player.ATTR_INPUT_SOURCE: media_input,
    }

    await hass.services.async_call(
        entity.domain,
        media_player.SERVICE_SELECT_SOURCE,
        data,
        blocking=False,
        context=context,
    )

    return directive.response()