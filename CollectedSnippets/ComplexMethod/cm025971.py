async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Tag component."""
    component = EntityComponent[TagEntity](LOGGER, DOMAIN, hass)
    id_manager = TagIDManager()
    hass.data[TAG_DATA] = storage_collection = TagStorageCollection(
        TagStore(
            hass, STORAGE_VERSION, STORAGE_KEY, minor_version=STORAGE_VERSION_MINOR
        ),
        id_manager,
    )
    await storage_collection.async_load()
    TagDictStorageCollectionWebsocket(
        storage_collection, DOMAIN, DOMAIN, CREATE_FIELDS, UPDATE_FIELDS
    ).async_setup(hass)

    entity_registry = er.async_get(hass)
    entity_update_handlers: dict[str, Callable[[str | None, str | None], None]] = {}

    async def tag_change_listener(
        change_type: str, item_id: str, updated_config: dict
    ) -> None:
        """Tag storage change listener."""

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug(
                "%s, item: %s, update: %s", change_type, item_id, updated_config
            )
        if change_type == collection.CHANGE_ADDED:
            # When tags are added to storage
            entity = _create_entry(entity_registry, updated_config[CONF_ID], None)
            if TYPE_CHECKING:
                assert entity.original_name
            await component.async_add_entities(
                [
                    TagEntity(
                        entity_update_handlers,
                        entity.name or entity.original_name,
                        updated_config[CONF_ID],
                        updated_config.get(LAST_SCANNED),
                        updated_config.get(DEVICE_ID),
                    )
                ]
            )

        elif change_type == collection.CHANGE_UPDATED:
            # When tags are changed or updated in storage
            if handler := entity_update_handlers.get(updated_config[CONF_ID]):
                handler(
                    updated_config.get(DEVICE_ID),
                    updated_config.get(LAST_SCANNED),
                )

        # Deleted tags
        elif change_type == collection.CHANGE_REMOVED:
            # When tags are removed from storage
            entity_id = entity_registry.async_get_entity_id(
                DOMAIN, DOMAIN, updated_config[CONF_ID]
            )
            if entity_id:
                entity_registry.async_remove(entity_id)

    storage_collection.async_add_listener(tag_change_listener)

    entities: list[TagEntity] = []
    for tag in storage_collection.async_items():
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Adding tag: %s", tag)
        entity_id = entity_registry.async_get_entity_id(DOMAIN, DOMAIN, tag[CONF_ID])
        if entity_id := entity_registry.async_get_entity_id(
            DOMAIN, DOMAIN, tag[CONF_ID]
        ):
            entity = entity_registry.async_get(entity_id)
        else:
            entity = _create_entry(entity_registry, tag[CONF_ID], None)
        if TYPE_CHECKING:
            assert entity
            assert entity.original_name
        name = entity.name or entity.original_name
        entities.append(
            TagEntity(
                entity_update_handlers,
                name,
                tag[CONF_ID],
                tag.get(LAST_SCANNED),
                tag.get(DEVICE_ID),
            )
        )
    await component.async_add_entities(entities)

    return True