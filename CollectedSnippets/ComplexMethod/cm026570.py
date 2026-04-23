async def _async_reset_energy_counter(service: ServiceCall):
    """Service to reset the energy counter."""
    entity_id_list = service.data[ATTR_ENTITY_ID]

    entry: HomematicIPConfigEntry
    for entry in service.hass.config_entries.async_loaded_entries(DOMAIN):
        if entity_id_list != "all":
            for entity_id in entity_id_list:
                device = entry.runtime_data.hmip_device_by_entity_id.get(entity_id)
                if device and isinstance(device, SwitchMeasuring):
                    await device.reset_energy_counter_async()
        else:
            for device in entry.runtime_data.home.devices:
                if isinstance(device, SwitchMeasuring):
                    await device.reset_energy_counter_async()