def async_migrate_unique_ids(
    coordinator: ShellyRpcCoordinator | ShellyBlockCoordinator,
    entity_entry: er.RegistryEntry,
) -> dict[str, Any] | None:
    """Migrate button unique IDs."""
    if not entity_entry.entity_id.startswith("button"):
        return None

    for key in ("reboot", "self_test", "mute", "unmute"):
        old_unique_id = f"{coordinator.mac}_{key}"
        if entity_entry.unique_id == old_unique_id:
            new_unique_id = f"{coordinator.mac}-{key}"
            LOGGER.debug(
                "Migrating unique_id for %s entity from [%s] to [%s]",
                entity_entry.entity_id,
                old_unique_id,
                new_unique_id,
            )
            return {
                "new_unique_id": entity_entry.unique_id.replace(
                    old_unique_id, new_unique_id
                )
            }

    if not isinstance(coordinator, ShellyRpcCoordinator):
        return None

    if blutrv_key_ids := get_rpc_key_ids(coordinator.device.status, BLU_TRV_IDENTIFIER):
        for _id in blutrv_key_ids:
            key = f"{BLU_TRV_IDENTIFIER}:{_id}"
            ble_addr: str = coordinator.device.config[key]["addr"]
            old_unique_id = f"{ble_addr}_calibrate"
            if entity_entry.unique_id == old_unique_id:
                new_unique_id = f"{format_ble_addr(ble_addr)}-{key}-calibrate"
                LOGGER.debug(
                    "Migrating unique_id for %s entity from [%s] to [%s]",
                    entity_entry.entity_id,
                    old_unique_id,
                    new_unique_id,
                )
                return {
                    "new_unique_id": entity_entry.unique_id.replace(
                        old_unique_id, new_unique_id
                    )
                }

    if virtual_button_keys := get_rpc_key_instances(
        coordinator.device.config, "button"
    ):
        for key in virtual_button_keys:
            old_unique_id = f"{coordinator.mac}-{key}"
            if entity_entry.unique_id == old_unique_id:
                role = get_rpc_role_by_key(coordinator.device.config, key)
                new_unique_id = f"{coordinator.mac}-{key}-button_{role}"
                LOGGER.debug(
                    "Migrating unique_id for %s entity from [%s] to [%s]",
                    entity_entry.entity_id,
                    old_unique_id,
                    new_unique_id,
                )
                return {
                    "new_unique_id": entity_entry.unique_id.replace(
                        old_unique_id, new_unique_id
                    )
                }

    return None