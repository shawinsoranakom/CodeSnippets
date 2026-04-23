async def async_scan_tag(
    hass: HomeAssistant,
    tag_id: str,
    device_id: str | None,
    context: Context | None = None,
) -> None:
    """Handle when a tag is scanned."""
    if DOMAIN not in hass.config.components:
        raise HomeAssistantError("tag component has not been set up.")

    storage_collection = hass.data[TAG_DATA]
    entity_registry = er.async_get(hass)
    entity_id = entity_registry.async_get_entity_id(DOMAIN, DOMAIN, tag_id)

    # Get name from entity registry, default value None if not present
    tag_name = None
    if entity_id and (entity := entity_registry.async_get(entity_id)):
        tag_name = entity.name or entity.original_name

    hass.bus.async_fire(
        EVENT_TAG_SCANNED,
        {TAG_ID: tag_id, CONF_NAME: tag_name, DEVICE_ID: device_id},
        context=context,
    )

    extra_kwargs = {}
    if device_id:
        extra_kwargs[DEVICE_ID] = device_id
    if tag_id in storage_collection.data:
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Updating tag %s with extra %s", tag_id, extra_kwargs)
        await storage_collection.async_update_item(
            tag_id, {LAST_SCANNED: dt_util.utcnow(), **extra_kwargs}
        )
    else:
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Creating tag %s with extra %s", tag_id, extra_kwargs)
        await storage_collection.async_create_item(
            {TAG_ID: tag_id, LAST_SCANNED: dt_util.utcnow(), **extra_kwargs}
        )
    _LOGGER.debug("Tag: %s scanned by device: %s", tag_id, device_id)