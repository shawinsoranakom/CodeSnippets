def migrate_entity_ids(
    hass: HomeAssistant, config_entry_id: str, host: ReolinkHost
) -> None:
    """Migrate entity IDs if needed."""
    device_reg = dr.async_get(hass)
    devices = dr.async_entries_for_config_entry(device_reg, config_entry_id)
    ch_device_ids = {}
    for device in devices:
        (device_uid, ch, is_chime) = get_device_uid_and_ch(device, host)

        if host.api.supported(None, "UID") and device_uid[0] != host.unique_id:
            if ch is None:
                new_device_id = f"{host.unique_id}"
            else:
                new_device_id = f"{host.unique_id}_{device_uid[1]}"
            _LOGGER.debug(
                "Updating Reolink device UID from %s to %s",
                device_uid,
                new_device_id,
            )
            new_identifiers = {(DOMAIN, new_device_id)}
            device_reg.async_update_device(device.id, new_identifiers=new_identifiers)

        # Check for wrongfully combined entities in one device
        # Can be removed in HA 2025.12
        new_identifiers = device.identifiers.copy()
        remove_ids = False
        if (DOMAIN, host.unique_id) in device.identifiers:
            remove_ids = True  # NVR/Hub in identifiers, keep that one, remove others
        for old_id in device.identifiers:
            (old_device_uid, _old_ch, _old_is_chime) = get_device_uid_and_ch(
                old_id, host
            )
            if (
                not old_device_uid
                or old_device_uid[0] != host.unique_id
                or old_id[1] == host.unique_id
            ):
                continue
            if remove_ids:
                new_identifiers.remove(old_id)
            remove_ids = True  # after the first identifier, remove the others
        if new_identifiers != device.identifiers:
            _LOGGER.debug(
                "Updating Reolink device identifiers from %s to %s",
                device.identifiers,
                new_identifiers,
            )
            device_reg.async_update_device(device.id, new_identifiers=new_identifiers)
            break

        if ch is None or is_chime:
            continue  # Do not consider the NVR itself or chimes

        # Check for wrongfully added MAC of the NVR/Hub to the camera
        # Can be removed in HA 2025.12
        host_connnection = (CONNECTION_NETWORK_MAC, host.api.mac_address)
        if host_connnection in device.connections:
            new_connections = device.connections.copy()
            new_connections.remove(host_connnection)
            _LOGGER.debug(
                "Updating Reolink device connections from %s to %s",
                device.connections,
                new_connections,
            )
            device_reg.async_update_device(device.id, new_connections=new_connections)

        ch_device_ids[device.id] = ch
        if host.api.supported(ch, "UID") and device_uid[1] != host.api.camera_uid(ch):
            if host.api.supported(None, "UID"):
                new_device_id = f"{host.unique_id}_{host.api.camera_uid(ch)}"
            else:
                new_device_id = f"{device_uid[0]}_{host.api.camera_uid(ch)}"
            _LOGGER.debug(
                "Updating Reolink device UID from %s to %s",
                device_uid,
                new_device_id,
            )
            new_identifiers = {(DOMAIN, new_device_id)}
            existing_device = device_reg.async_get_device(identifiers=new_identifiers)
            if existing_device is None:
                device_reg.async_update_device(
                    device.id, new_identifiers=new_identifiers
                )
            else:
                _LOGGER.warning(
                    "Reolink device with uid %s already exists, "
                    "removing device with uid %s",
                    new_device_id,
                    device_uid,
                )
                device_reg.async_remove_device(device.id)

    entity_reg = er.async_get(hass)
    entities = er.async_entries_for_config_entry(entity_reg, config_entry_id)
    for entity in entities:
        if host.api.supported(None, "UID") and not entity.unique_id.startswith(
            host.unique_id
        ):
            new_id = f"{host.unique_id}_{entity.unique_id.split('_', 1)[1]}"
            _LOGGER.debug(
                "Updating Reolink entity unique_id from %s to %s",
                entity.unique_id,
                new_id,
            )
            existing_entity = entity_reg.async_get_entity_id(
                entity.domain, entity.platform, new_id
            )
            if existing_entity is None:
                entity_reg.async_update_entity(entity.entity_id, new_unique_id=new_id)
            else:
                _LOGGER.warning(
                    "Reolink entity with unique_id %s already exists, "
                    "removing entity with unique_id %s",
                    new_id,
                    entity.unique_id,
                )
                entity_reg.async_remove(entity.entity_id)
                continue

        if entity.device_id in ch_device_ids:
            ch = ch_device_ids[entity.device_id]
            id_parts = entity.unique_id.split("_", 2)
            if len(id_parts) < 3:
                _LOGGER.warning(
                    "Reolink channel %s entity has unexpected unique_id format %s, with device id %s",
                    ch,
                    entity.unique_id,
                    entity.device_id,
                )
                continue
            if host.api.supported(ch, "UID") and id_parts[1] != host.api.camera_uid(ch):
                new_id = f"{host.unique_id}_{host.api.camera_uid(ch)}_{id_parts[2]}"
                _LOGGER.debug(
                    "Updating Reolink entity unique_id from %s to %s",
                    entity.unique_id,
                    new_id,
                )
                existing_entity = entity_reg.async_get_entity_id(
                    entity.domain, entity.platform, new_id
                )
                if existing_entity is None:
                    entity_reg.async_update_entity(
                        entity.entity_id, new_unique_id=new_id
                    )
                else:
                    _LOGGER.warning(
                        "Reolink entity with unique_id %s already exists, "
                        "removing entity with unique_id %s",
                        new_id,
                        entity.unique_id,
                    )
                    entity_reg.async_remove(entity.entity_id)