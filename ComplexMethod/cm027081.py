async def async_setup_entry(hass: HomeAssistant, entry: SwitchbotConfigEntry) -> bool:
    """Set up Switchbot from a config entry."""
    assert entry.unique_id is not None
    if CONF_ADDRESS not in entry.data and CONF_MAC in entry.data:
        # Bleak uses addresses not mac addresses which are actually
        # UUIDs on some platforms (MacOS).
        mac = entry.data[CONF_MAC]
        if "-" not in mac:
            mac = dr.format_mac(mac)
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_ADDRESS: mac},
        )

    # Migrate deprecated air purifier sensor types introduced before pySwitchbot 2.0.0.
    if entry.data.get(CONF_SENSOR_TYPE) in (
        DEPRECATED_SENSOR_TYPE_AIR_PURIFIER,
        DEPRECATED_SENSOR_TYPE_AIR_PURIFIER_TABLE,
    ) and not _migrate_deprecated_air_purifier_type(hass, entry):
        # Device was not in range; retry when it starts advertising again.
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={
                "sensor_type": entry.data[CONF_SENSOR_TYPE],
                "address": entry.data[CONF_ADDRESS],
            },
        )

    sensor_type: str = entry.data[CONF_SENSOR_TYPE]
    switchbot_model = HASS_SENSOR_TYPE_TO_SWITCHBOT_MODEL[sensor_type]
    # connectable means we can make connections to the device
    connectable = (
        switchbot_model in CONNECTABLE_SUPPORTED_MODEL_TYPES
        and switchbot_model not in NON_CONNECTABLE_SUPPORTED_MODEL_TYPES
    )
    address: str = entry.data[CONF_ADDRESS]

    await switchbot.close_stale_connections_by_address(address)

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address.upper(), connectable
    )
    if not ble_device:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found_error",
            translation_placeholders={"sensor_type": sensor_type, "address": address},
        )

    cls = CLASS_BY_DEVICE.get(sensor_type, switchbot.SwitchbotDevice)
    if switchbot_model in ENCRYPTED_MODELS:
        try:
            device = cls(
                device=ble_device,
                key_id=entry.data.get(CONF_KEY_ID),
                encryption_key=entry.data.get(CONF_ENCRYPTION_KEY),
                retry_count=entry.options[CONF_RETRY_COUNT],
                model=switchbot_model,
            )
        except ValueError as error:
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="value_error",
                translation_placeholders={"error": str(error)},
            ) from error
    else:
        device = cls(
            device=ble_device,
            password=entry.data.get(CONF_PASSWORD),
            retry_count=entry.options[CONF_RETRY_COUNT],
        )

    coordinator = entry.runtime_data = SwitchbotDataUpdateCoordinator(
        hass,
        _LOGGER,
        ble_device,
        device,
        entry.unique_id,
        entry.data.get(CONF_NAME, entry.title),
        connectable,
        switchbot_model,
        entry,
    )
    entry.async_on_unload(coordinator.async_start())
    if not await coordinator.async_wait_ready():
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="advertising_state_error",
            translation_placeholders={"address": address},
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS_BY_TYPE[sensor_type]
    )

    return True