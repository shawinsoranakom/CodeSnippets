def async_get_config_entry_for_service_call(
    call: ServiceCall,
) -> ShellyConfigEntry:
    """Get the config entry related to a service call (by device ID)."""
    device_registry = dr.async_get(call.hass)
    device_id = call.data[ATTR_DEVICE_ID]

    if (device_entry := device_registry.async_get(device_id)) is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_device_id",
            translation_placeholders={"device_id": device_id},
        )

    for entry_id in device_entry.config_entries:
        config_entry = call.hass.config_entries.async_get_entry(entry_id)

        if TYPE_CHECKING:
            assert config_entry

        if config_entry.domain != DOMAIN:
            continue
        if config_entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
                translation_placeholders={"device": config_entry.title},
            )
        if get_device_entry_gen(config_entry) not in RPC_GENERATIONS:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="kvs_not_supported",
                translation_placeholders={"device": config_entry.title},
            )
        if config_entry.data.get(CONF_SLEEP_PERIOD, 0) > 0:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="kvs_not_supported",
                translation_placeholders={"device": config_entry.title},
            )
        return config_entry

    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="config_entry_not_found",
        translation_placeholders={"device_id": device_id},
    )