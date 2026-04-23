async def set_hot_water_schedule(service_call: ServiceCall) -> None:
    """Set hot water heating schedule."""
    device_id = service_call.data[ATTR_DEVICE_ID]

    # Get the device and config entry
    device_registry = dr.async_get(service_call.hass)
    device_entry = device_registry.async_get(device_id)

    if device_entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_device_id",
            translation_placeholders={"device_id": device_id},
        )

    # Find the config entry for this device
    matching_entries: list[BSBLanConfigEntry] = [
        entry
        for entry in service_call.hass.config_entries.async_entries(DOMAIN)
        if entry.entry_id in device_entry.config_entries
    ]

    if not matching_entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry_for_device",
            translation_placeholders={"device_id": device_entry.name or device_id},
        )

    entry = matching_entries[0]

    # Verify the config entry is loaded
    if entry.state is not ConfigEntryState.LOADED:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_loaded",
            translation_placeholders={"device_name": device_entry.name or device_id},
        )

    client = entry.runtime_data.client

    # Convert time slots to DaySchedule objects
    monday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_MONDAY_SLOTS)
    )
    tuesday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_TUESDAY_SLOTS)
    )
    wednesday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_WEDNESDAY_SLOTS)
    )
    thursday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_THURSDAY_SLOTS)
    )
    friday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_FRIDAY_SLOTS)
    )
    saturday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_SATURDAY_SLOTS)
    )
    sunday = _convert_time_slots_to_day_schedule(
        service_call.data.get(ATTR_SUNDAY_SLOTS)
    )

    # Create the DHWSchedule object
    dhw_schedule = DHWSchedule(
        monday=monday,
        tuesday=tuesday,
        wednesday=wednesday,
        thursday=thursday,
        friday=friday,
        saturday=saturday,
        sunday=sunday,
    )

    LOGGER.debug(
        "Setting hot water schedule - Monday: %s, Tuesday: %s, Wednesday: %s, "
        "Thursday: %s, Friday: %s, Saturday: %s, Sunday: %s",
        monday,
        tuesday,
        wednesday,
        thursday,
        friday,
        saturday,
        sunday,
    )

    try:
        # Call the BSB-LAN API to set the schedule
        await client.set_hot_water_schedule(dhw_schedule)
    except BSBLANError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="set_schedule_failed",
            translation_placeholders={"error": str(err)},
        ) from err

    # Refresh the slow coordinator to get the updated schedule
    await entry.runtime_data.slow_coordinator.async_request_refresh()