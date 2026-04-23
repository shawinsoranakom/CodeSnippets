def _get_registry_entries(
    hass: HomeAssistant, entity_id: str
) -> tuple[
    er.RegistryEntry | None,
    dr.DeviceEntry | None,
    ar.AreaEntry | None,
]:
    """Get registry entries."""
    ent_reg = er.async_get(hass)
    dev_reg = dr.async_get(hass)
    area_reg = ar.async_get(hass)

    if (entity_entry := ent_reg.async_get(entity_id)) and entity_entry.device_id:
        device_entry = dev_reg.devices.get(entity_entry.device_id)
    else:
        device_entry = None

    if entity_entry and entity_entry.area_id:
        area_id = entity_entry.area_id
    elif device_entry and device_entry.area_id:
        area_id = device_entry.area_id
    else:
        area_id = None

    if area_id is not None:
        area_entry = area_reg.async_get_area(area_id)
    else:
        area_entry = None

    return entity_entry, device_entry, area_entry