async def async_migrate_entry(hass: HomeAssistant, entry: PortainerConfigEntry) -> bool:
    """Migrate old entry."""

    if entry.version < 2:
        data = dict(entry.data)
        data[CONF_URL] = data.pop(CONF_HOST)
        data[CONF_API_TOKEN] = data.pop(CONF_API_KEY)
        hass.config_entries.async_update_entry(entry=entry, data=data, version=2)

    if entry.version < 3:
        data = dict(entry.data)
        data[CONF_VERIFY_SSL] = True
        hass.config_entries.async_update_entry(entry=entry, data=data, version=3)

    if entry.version < 4:
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)
        devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
        for device in devices:
            # This means it's an endpoint. This can be skipped, we're only interested in the containers
            if device.via_device_id is None:
                continue

            parent_devices = device_registry.async_get(device.via_device_id)
            assert parent_devices
            for parent_device in parent_devices.identifiers:
                if parent_device[0] == DOMAIN:
                    parent_device_identifiers = parent_device
                    break

            _LOGGER.debug("Parent device identifiers: %s", parent_device_identifiers)
            endpoint_id = parent_device_identifiers[1].split("_")[-1]
            _LOGGER.debug("Endpoint ID: %s", endpoint_id)
            current_identifier = next(iter(device.identifiers))
            _LOGGER.debug("Current identifier: %s", current_identifier)
            container = current_identifier[1].split("_", 1)[1]
            _LOGGER.debug("Container name: %s", container)
            new_identifier = f"{entry.entry_id}_{endpoint_id}_{container}"
            _LOGGER.debug("New identifier: %s", new_identifier)

            new_identifiers = set(device.identifiers)
            new_identifiers.add((DOMAIN, new_identifier))

            device_registry.async_update_device(
                device.id,
                new_identifiers=new_identifiers,
            )

            # Now also update the underlying entities with the new unique_attr_id
            entities_device = er.async_entries_for_device(
                entity_registry,
                device.id,
            )
            for entity in entities_device:
                _LOGGER.debug("Handling entity: %s", entity)
                # This time we also also have a rest tail (for instance _firefly_iii_db)
                _, _, rest_tail = entity.unique_id.split("_", 2)
                new_unique_id = f"{new_identifier}_{rest_tail}"
                _LOGGER.debug("New unique ID: %s", new_unique_id)
                entity_registry.async_update_entity(
                    entity_id=entity.entity_id, new_unique_id=new_unique_id
                )

        hass.config_entries.async_update_entry(entry=entry, version=4)

    if entry.version < 5:
        client = Portainer(
            api_url=entry.data[CONF_URL],
            api_key=entry.data[CONF_API_TOKEN],
            session=async_create_clientsession(
                hass=hass, verify_ssl=entry.data[CONF_VERIFY_SSL]
            ),
        )
        try:
            system_status = await client.portainer_system_status()
        except PortainerError:
            _LOGGER.exception("Failed to fetch instance ID during migration")
            return False

        hass.config_entries.async_update_entry(
            entry=entry,
            unique_id=system_status.instance_id,
            version=5,
        )

    return True