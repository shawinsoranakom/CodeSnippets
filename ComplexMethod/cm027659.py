def resolve_area_id(hass: HomeAssistant, lookup_value: Any) -> str | None:
    """Resolve lookup value to an area ID.

    Accepts area name, area alias, device ID, or entity ID.
    Returns the area ID or None if not found.
    """
    area_reg = ar.async_get(hass)
    dev_reg = dr.async_get(hass)
    ent_reg = er.async_get(hass)
    lookup_str = str(lookup_value)

    # Check if it's an area name
    if area := area_reg.async_get_area_by_name(lookup_str):
        return area.id

    # Check if it's an area alias
    areas_list = area_reg.async_get_areas_by_alias(lookup_str)
    if areas_list:
        return areas_list[0].id

    # Check if it's an entity ID
    try:
        cv.entity_id(lookup_value)
    except vol.Invalid:
        pass
    else:
        if entity := ent_reg.async_get(lookup_value):
            # If entity has an area ID, return that
            if entity.area_id:
                return entity.area_id
            # If entity has a device ID, return the area ID for the device
            if entity.device_id and (device := dev_reg.async_get(entity.device_id)):
                return device.area_id

    # Check if it's a device ID
    if device := dev_reg.async_get(lookup_value):
        return device.area_id

    return None