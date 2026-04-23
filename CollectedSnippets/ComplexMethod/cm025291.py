async def async_migrate_entry(
    hass: HomeAssistant, config_entry: LcnConfigEntry
) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    new_data = {**config_entry.data}

    if config_entry.version == 1:
        # update to 1.2  (add acknowledge flag)
        if config_entry.minor_version < 2:
            new_data[CONF_ACKNOWLEDGE] = False

    if config_entry.version < 2:
        # update to 2.1  (fix transitions for lights and switches)
        new_entities_data = [*new_data[CONF_ENTITIES]]
        for entity in new_entities_data:
            if entity[CONF_DOMAIN] in [Platform.LIGHT, Platform.SCENE]:
                if entity[CONF_DOMAIN_DATA][CONF_TRANSITION] is None:
                    entity[CONF_DOMAIN_DATA][CONF_TRANSITION] = 0
                entity[CONF_DOMAIN_DATA][CONF_TRANSITION] /= 1000.0
        new_data[CONF_ENTITIES] = new_entities_data

    if config_entry.version < 3:
        # update to 3.1 (remove resource parameter, add climate target lock value parameter)
        for entity in new_data[CONF_ENTITIES]:
            entity.pop(CONF_RESOURCE, None)

            if entity[CONF_DOMAIN] == Platform.CLIMATE:
                entity[CONF_DOMAIN_DATA].setdefault(CONF_TARGET_VALUE_LOCKED, -1)

        # migrate climate and scene unique ids
        await async_migrate_entities(hass, config_entry)

    hass.config_entries.async_update_entry(
        config_entry, data=new_data, minor_version=1, version=3
    )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )
    return True