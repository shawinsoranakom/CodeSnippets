async def async_migrate_entry(hass: HomeAssistant, entry: ScrapeConfigEntry) -> bool:
    """Migrate old entry."""

    if entry.version > 2:
        # Don't migrate from future version
        return False

    if entry.version == 1:
        old_to_new_sensor_id = {}
        for sensor_config in entry.options[SENSOR_DOMAIN]:
            # Create a new sub config entry per sensor
            title = sensor_config[CONF_NAME]
            old_unique_id = sensor_config[CONF_UNIQUE_ID]
            subentry_config = {
                CONF_INDEX: sensor_config[CONF_INDEX],
                CONF_SELECT: sensor_config[CONF_SELECT],
                CONF_ADVANCED: {},
            }

            for sensor_advanced_key in (
                CONF_ATTRIBUTE,
                CONF_VALUE_TEMPLATE,
                CONF_AVAILABILITY,
                CONF_DEVICE_CLASS,
                CONF_STATE_CLASS,
                CONF_UNIT_OF_MEASUREMENT,
            ):
                if sensor_advanced_key not in sensor_config:
                    continue
                subentry_config[CONF_ADVANCED][sensor_advanced_key] = sensor_config[
                    sensor_advanced_key
                ]

            new_sub_entry = ConfigSubentry(
                data=MappingProxyType(subentry_config),
                subentry_type="entity",
                title=title,
                unique_id=None,
            )
            _LOGGER.debug(
                "Migrating sensor %s with unique id %s to sub config entry id %s, old data %s, new data %s",
                title,
                old_unique_id,
                new_sub_entry.subentry_id,
                sensor_config,
                subentry_config,
            )
            old_to_new_sensor_id[old_unique_id] = new_sub_entry.subentry_id
            hass.config_entries.async_add_subentry(entry, new_sub_entry)

        # Use the new sub config entry id as the unique id for the sensor entity
        entity_reg = er.async_get(hass)
        entities = er.async_entries_for_config_entry(entity_reg, entry.entry_id)
        for entity in entities:
            if (old_unique_id := entity.unique_id) in old_to_new_sensor_id:
                new_unique_id = old_to_new_sensor_id[old_unique_id]
                _LOGGER.debug(
                    "Migrating entity %s with unique id %s to new unique id %s",
                    entity.entity_id,
                    entity.unique_id,
                    new_unique_id,
                )
                entity_reg.async_update_entity(
                    entity.entity_id,
                    config_entry_id=entry.entry_id,
                    config_subentry_id=new_unique_id,
                    new_unique_id=new_unique_id,
                )

        # Use the new sub config entry id as the identifier for the sensor device
        device_reg = dr.async_get(hass)
        devices = dr.async_entries_for_config_entry(device_reg, entry.entry_id)
        for device in devices:
            for domain, identifier in device.identifiers:
                if domain != DOMAIN or identifier not in old_to_new_sensor_id:
                    continue

                subentry_id = old_to_new_sensor_id[identifier]
                new_identifiers = deepcopy(device.identifiers)
                new_identifiers.remove((domain, identifier))
                new_identifiers.add((domain, old_to_new_sensor_id[identifier]))
                _LOGGER.debug(
                    "Migrating device %s with identifiers %s to new identifiers %s",
                    device.id,
                    device.identifiers,
                    new_identifiers,
                )
                device_reg.async_update_device(
                    device.id,
                    add_config_entry_id=entry.entry_id,
                    add_config_subentry_id=subentry_id,
                    new_identifiers=new_identifiers,
                )

                # Removing None from the list of subentries if existing
                # as the device should only belong to the subentry
                # and not the main config entry
                device_reg.async_update_device(
                    device.id,
                    remove_config_entry_id=entry.entry_id,
                    remove_config_subentry_id=None,
                )

        # Update the resource config
        new_config_entry_data = dict(entry.options)
        new_config_entry_data[CONF_AUTH] = {}
        new_config_entry_data[CONF_ADVANCED] = {}
        new_config_entry_data.pop(SENSOR_DOMAIN, None)
        for resource_advanced_key in (
            CONF_HEADERS,
            CONF_VERIFY_SSL,
            CONF_TIMEOUT,
            CONF_ENCODING,
        ):
            if resource_advanced_key in new_config_entry_data:
                new_config_entry_data[CONF_ADVANCED][resource_advanced_key] = (
                    new_config_entry_data.pop(resource_advanced_key)
                )
        for resource_auth_key in (CONF_AUTHENTICATION, CONF_USERNAME, CONF_PASSWORD):
            if resource_auth_key in new_config_entry_data:
                new_config_entry_data[CONF_AUTH][resource_auth_key] = (
                    new_config_entry_data.pop(resource_auth_key)
                )

        _LOGGER.debug(
            "Migrating config entry %s from version 1 to version 2 with data %s",
            entry.entry_id,
            new_config_entry_data,
        )
        hass.config_entries.async_update_entry(
            entry, version=2, options=new_config_entry_data
        )

    return True