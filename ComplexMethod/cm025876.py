async def async_remove_orphaned_entries_service(hub: DeconzHub) -> None:
    """Remove orphaned deCONZ entries from device and entity registries."""
    device_registry = dr.async_get(hub.hass)
    entity_registry = er.async_get(hub.hass)

    entity_entries = er.async_entries_for_config_entry(
        entity_registry, hub.config_entry.entry_id
    )

    entities_to_be_removed = []
    devices_to_be_removed = [
        entry.id
        for entry in device_registry.devices.get_devices_for_config_entry_id(
            hub.config_entry.entry_id
        )
    ]

    # Don't remove the Gateway service entry
    hub_service = device_registry.async_get_device(
        identifiers={(DOMAIN, hub.api.config.bridge_id)}
    )
    if hub_service and hub_service.id in devices_to_be_removed:
        devices_to_be_removed.remove(hub_service.id)

    # Don't remove devices belonging to available events
    for event in hub.events:
        if event.device_id in devices_to_be_removed:
            devices_to_be_removed.remove(event.device_id)

    for entry in entity_entries:
        # Don't remove available entities
        if entry.unique_id in hub.entities[entry.domain]:
            # Don't remove devices with available entities
            if entry.device_id in devices_to_be_removed:
                devices_to_be_removed.remove(entry.device_id)
            continue
        # Remove entities that are not available
        entities_to_be_removed.append(entry.entity_id)

    # Remove unavailable entities
    for entity_id in entities_to_be_removed:
        entity_registry.async_remove(entity_id)

    # Remove devices that don't belong to any entity
    for device_id in devices_to_be_removed:
        if (
            len(
                er.async_entries_for_device(
                    entity_registry, device_id, include_disabled_entities=True
                )
            )
            == 0
        ):
            device_registry.async_remove_device(device_id)