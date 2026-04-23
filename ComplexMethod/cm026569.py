async def _set_active_climate_profile(service: ServiceCall) -> None:
    """Service to set the active climate profile."""
    entity_id_list = service.data[ATTR_ENTITY_ID]
    climate_profile_index = service.data[ATTR_CLIMATE_PROFILE_INDEX] - 1

    entry: HomematicIPConfigEntry
    for entry in service.hass.config_entries.async_loaded_entries(DOMAIN):
        if entity_id_list != "all":
            for entity_id in entity_id_list:
                group = entry.runtime_data.hmip_device_by_entity_id.get(entity_id)
                if group and isinstance(group, HeatingGroup):
                    await group.set_active_profile_async(climate_profile_index)
        else:
            for group in entry.runtime_data.home.groups:
                if isinstance(group, HeatingGroup):
                    await group.set_active_profile_async(climate_profile_index)