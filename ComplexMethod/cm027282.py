def async_migrate(hass: HomeAssistant, address: str, sensor_name: str) -> None:
    """Migrate entities to new unique ids (with BLE Address)."""
    ent_reg = er.async_get(hass)
    unique_id_trailer = f"_{sensor_name}"
    new_unique_id = f"{address}{unique_id_trailer}"
    if ent_reg.async_get_entity_id(DOMAIN, Platform.SENSOR, new_unique_id):
        # New unique id already exists
        return
    dev_reg = dr.async_get(hass)
    if not (
        device := dev_reg.async_get_device(
            connections={(CONNECTION_BLUETOOTH, address)}
        )
    ):
        return
    entities = async_entries_for_device(
        ent_reg,
        device_id=device.id,
        include_disabled_entities=True,
    )
    matching_reg_entry: RegistryEntry | None = None
    for entry in entities:
        if entry.unique_id.endswith(unique_id_trailer) and (
            not matching_reg_entry or "(" not in entry.unique_id
        ):
            matching_reg_entry = entry
    if not matching_reg_entry or matching_reg_entry.unique_id == new_unique_id:
        # Already has the newest unique id format
        return
    entity_id = matching_reg_entry.entity_id
    ent_reg.async_update_entity(entity_id=entity_id, new_unique_id=new_unique_id)
    _LOGGER.debug("Migrated entity '%s' to unique id '%s'", entity_id, new_unique_id)