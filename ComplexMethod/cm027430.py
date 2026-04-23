def get_vehicle_proxy(service_call: ServiceCall) -> RenaultVehicleProxy:
    """Get vehicle from service_call data."""
    device_registry = dr.async_get(service_call.hass)
    device_id = service_call.data[ATTR_VEHICLE]
    device_entry = device_registry.async_get(device_id)
    if device_entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_device_id",
            translation_placeholders={"device_id": device_id},
        )

    loaded_entries: list[RenaultConfigEntry] = [
        entry
        for entry in service_call.hass.config_entries.async_loaded_entries(DOMAIN)
        if entry.entry_id in device_entry.config_entries
    ]
    for entry in loaded_entries:
        for vin, vehicle in entry.runtime_data.vehicles.items():
            if (DOMAIN, vin) in device_entry.identifiers:
                return vehicle
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="no_config_entry_for_device",
        translation_placeholders={"device_id": device_entry.name or device_id},
    )