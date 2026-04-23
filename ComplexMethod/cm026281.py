def async_static_info_updated(
    hass: HomeAssistant,
    entry_data: RuntimeEntryData,
    platform: entity_platform.EntityPlatform,
    async_add_entities: AddEntitiesCallback,
    info_type: type[_InfoT],
    entity_type: type[_EntityT],
    state_type: type[_StateT],
    infos: list[EntityInfo],
) -> None:
    """Update entities of this platform when entities are listed."""
    current_infos = entry_data.info[info_type]
    device_info = entry_data.device_info
    if TYPE_CHECKING:
        assert device_info is not None
    new_infos: dict[DeviceEntityKey, EntityInfo] = {}
    add_entities: list[_EntityT] = []

    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)

    # Track info by (info.device_id, info.key) to properly handle entities
    # moving between devices and support sub-devices with overlapping keys
    for info in infos:
        info_key = (info.device_id, info.key)
        new_infos[info_key] = info

        # Try to find existing entity - first with current device_id
        old_info = current_infos.pop(info_key, None)

        # If not found, search for entity with same key but different device_id
        # This handles the case where entity moved between devices
        if not old_info:
            for existing_device_id, existing_key in list(current_infos):
                if existing_key == info.key:
                    # Found entity with same key but different device_id
                    old_info = current_infos.pop((existing_device_id, existing_key))
                    break

        # Create new entity if it doesn't exist
        if not old_info:
            entity = entity_type(entry_data, info, state_type)
            add_entities.append(entity)
            continue

        # Entity exists - check if device_id has changed
        if old_info.device_id == info.device_id:
            continue

        # Entity has switched devices, need to migrate unique_id and handle state subscriptions
        old_unique_id = build_device_unique_id(device_info.mac_address, old_info)
        entity_id = ent_reg.async_get_entity_id(platform.domain, DOMAIN, old_unique_id)

        # If entity not found in registry, re-add it
        # This happens when the device_id changed and the old device was deleted
        if entity_id is None:
            _LOGGER.info(
                "Entity with old unique_id %s not found in registry after device_id "
                "changed from %s to %s, re-adding entity",
                old_unique_id,
                old_info.device_id,
                info.device_id,
            )
            entity = entity_type(entry_data, info, state_type)
            add_entities.append(entity)
            continue

        updates: dict[str, Any] = {}
        new_unique_id = build_device_unique_id(device_info.mac_address, info)

        # Update unique_id if it changed
        if old_unique_id != new_unique_id:
            updates["new_unique_id"] = new_unique_id

        # Update device assignment in registry
        if info.device_id:
            # Entity now belongs to a sub device
            new_device = dev_reg.async_get_device(
                identifiers={(DOMAIN, f"{device_info.mac_address}_{info.device_id}")}
            )
        else:
            # Entity now belongs to the main device
            new_device = dev_reg.async_get_device(
                connections={(dr.CONNECTION_NETWORK_MAC, device_info.mac_address)}
            )

        if new_device:
            updates["device_id"] = new_device.id

        # Apply all registry updates at once
        if updates:
            ent_reg.async_update_entity(entity_id, **updates)

        # IMPORTANT: The entity's device assignment in Home Assistant is only read when the entity
        # is first added. Updating the registry alone won't move the entity to the new device
        # in the UI. Additionally, the entity's state subscription is tied to the old device_id,
        # so it won't receive state updates for the new device_id.
        #
        # We must remove the old entity and re-add it to ensure:
        # 1. The entity appears under the correct device in the UI
        # 2. The entity's state subscription is updated to use the new device_id
        _LOGGER.debug(
            "Entity %s moving from device_id %s to %s",
            info.key,
            old_info.device_id,
            info.device_id,
        )

        # Signal the existing entity to remove itself
        # The entity is registered with the old device_id, so we signal with that
        entry_data.async_signal_entity_removal(info_type, old_info.device_id, info.key)

        # Create new entity with the new device_id
        add_entities.append(entity_type(entry_data, info, state_type))

    # Anything still in current_infos is now gone
    if current_infos:
        entry_data.async_remove_entities(
            hass, current_infos.values(), device_info.mac_address
        )

    # Then update the actual info
    entry_data.info[info_type] = new_infos

    if new_infos:
        entry_data.async_update_entity_infos(new_infos.values())

    if add_entities:
        # Add entities to Home Assistant
        async_add_entities(add_entities)