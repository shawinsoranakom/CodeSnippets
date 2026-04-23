async def async_handle(
    hass: HomeAssistant,
    platform: str,
    intent_type: str,
    slots: _SlotsType | None = None,
    text_input: str | None = None,
    context: Context | None = None,
    language: str | None = None,
    assistant: str | None = None,
    device_id: str | None = None,
    satellite_id: str | None = None,
    conversation_agent_id: str | None = None,
) -> IntentResponse:
    """Handle an intent."""
    handler = hass.data.get(DATA_KEY, {}).get(intent_type)

    if handler is None:
        raise UnknownIntent(f"Unknown intent {intent_type}")

    if context is None:
        context = Context()

    if language is None:
        language = hass.config.language

    intent = Intent(
        hass,
        platform=platform,
        intent_type=intent_type,
        slots=slots or {},
        text_input=text_input,
        context=context,
        language=language,
        assistant=assistant,
        device_id=device_id,
        satellite_id=satellite_id,
        conversation_agent_id=conversation_agent_id,
    )

    try:
        _LOGGER.info("Triggering intent handler %s", handler)
        result = await handler.async_handle(intent)
    except vol.Invalid as err:
        _LOGGER.warning("Received invalid slot info for %s: %s", intent_type, err)
        raise InvalidSlotInfo(f"Received invalid slot info for {intent_type}") from err
    except IntentError:
        raise  # bubble up intent related errors
    except Exception as err:
        _LOGGER.exception("Error handling %s", intent_type)
        raise IntentUnexpectedError(f"Error handling {intent_type}") from err
    return result