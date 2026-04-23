async def async_api_turn_on(
    hass: ha.HomeAssistant,
    config: AbstractConfig,
    directive: AlexaDirective,
    context: ha.Context,
) -> AlexaResponse:
    """Process a turn on request."""
    entity = directive.entity
    if (domain := entity.domain) == group.DOMAIN:
        domain = ha.DOMAIN

    service = SERVICE_TURN_ON
    if domain == cover.DOMAIN:
        service = cover.SERVICE_OPEN_COVER
    elif domain == climate.DOMAIN:
        service = climate.SERVICE_TURN_ON
    elif domain == fan.DOMAIN:
        service = fan.SERVICE_TURN_ON
    elif domain == humidifier.DOMAIN:
        service = humidifier.SERVICE_TURN_ON
    elif domain == remote.DOMAIN:
        service = remote.SERVICE_TURN_ON
    elif domain == vacuum.DOMAIN:
        supported = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        if (
            not supported & vacuum.VacuumEntityFeature.TURN_ON
            and supported & vacuum.VacuumEntityFeature.START
        ):
            service = vacuum.SERVICE_START
    elif domain == timer.DOMAIN:
        service = timer.SERVICE_START
    elif domain == media_player.DOMAIN:
        supported = entity.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        power_features = (
            media_player.MediaPlayerEntityFeature.TURN_ON
            | media_player.MediaPlayerEntityFeature.TURN_OFF
        )
        if not supported & power_features:
            service = media_player.SERVICE_MEDIA_PLAY

    await hass.services.async_call(
        domain,
        service,
        {ATTR_ENTITY_ID: entity.entity_id},
        blocking=False,
        context=context,
    )

    return directive.response()