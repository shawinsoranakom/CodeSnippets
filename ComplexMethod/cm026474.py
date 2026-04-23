async def async_api_turn_off(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a turn off request."""
    entity = directive.entity
    domain = entity.domain
    if entity.domain == group.DOMAIN:
        domain = ha.DOMAIN

    service = SERVICE_TURN_OFF
    if entity.domain == cover.DOMAIN:
        service = cover.SERVICE_CLOSE_COVER
    elif domain == climate.DOMAIN:
        service = climate.SERVICE_TURN_OFF
    elif domain == fan.DOMAIN:
        service = fan.SERVICE_TURN_OFF
    elif domain == remote.DOMAIN:
        service = remote.SERVICE_TURN_OFF
    elif domain == humidifier.DOMAIN:
        service = humidifier.SERVICE_TURN_OFF
    elif domain == vacuum.DOMAIN:
        supported = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if (
            not supported & vacuum.VacuumEntityFeature.TURN_OFF
            and supported & vacuum.VacuumEntityFeature.RETURN_HOME
        ):
            service = vacuum.SERVICE_RETURN_TO_BASE
    elif domain == timer.DOMAIN:
        service = timer.SERVICE_CANCEL
    elif domain == media_player.DOMAIN:
        supported = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        power_features = (
            media_player.MediaPlayerEntityFeature.TURN_ON
            | media_player.MediaPlayerEntityFeature.TURN_OFF
        )
        if not supported & power_features:
            service = media_player.SERVICE_MEDIA_STOP

    await hass.services.async_call(
        domain,
        service,
        {ATTR_ENTITY_ID: entity.entity_id},
        blocking=False,
        context=context,
    )

    return directive.response()