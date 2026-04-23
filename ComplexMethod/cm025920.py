async def async_migrate_devices_and_entities(
    hass: HomeAssistant, entry: ViCareConfigEntry, device: ViCareDevice
) -> None:
    """Migrate old entry."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    gateway_serial: str = device.config.getConfig().serial
    device_id = device.config.getId()
    device_serial: str | None = await hass.async_add_executor_job(
        get_device_serial, device.api
    )
    device_model = device.config.getModel()

    old_identifier = gateway_serial
    new_identifier = (
        f"{gateway_serial}_{device_serial if device_serial is not None else device_id}"
    )

    # Migrate devices
    for device_entry in dr.async_entries_for_config_entry(
        device_registry, entry.entry_id
    ):
        if (
            device_entry.identifiers == {(DOMAIN, old_identifier)}
            and device_entry.model == device_model
        ):
            _LOGGER.debug(
                "Migrating device %s to new identifier %s",
                device_entry.name,
                new_identifier,
            )
            device_registry.async_update_device(
                device_entry.id,
                serial_number=device_serial,
                new_identifiers={(DOMAIN, new_identifier)},
            )

            # Migrate entities
            for entity_entry in er.async_entries_for_device(
                entity_registry, device_entry.id, True
            ):
                if entity_entry.unique_id.startswith(new_identifier):
                    # already correct, nothing to do
                    continue
                unique_id_parts = entity_entry.unique_id.split("-")
                # replace old prefix `<gateway-serial>`
                # with `<gateways-serial>_<device-serial>`
                unique_id_parts[0] = new_identifier
                # convert climate entity unique id
                # from `<device_identifier>-<circuit_no>`
                # to `<device_identifier>-heating-<circuit_no>`
                if entity_entry.domain == CLIMATE_DOMAIN:
                    unique_id_parts[len(unique_id_parts) - 1] = (
                        f"{entity_entry.translation_key}-"
                        f"{unique_id_parts[len(unique_id_parts) - 1]}"
                    )
                entity_new_unique_id = "-".join(unique_id_parts)

                _LOGGER.debug(
                    "Migrating entity %s to new unique id %s",
                    entity_entry.name,
                    entity_new_unique_id,
                )
                entity_registry.async_update_entity(
                    entity_id=entity_entry.entity_id, new_unique_id=entity_new_unique_id
                )