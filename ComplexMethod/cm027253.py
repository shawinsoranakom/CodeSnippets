async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry for a bluetooth scanner."""
    if source_entry_id := entry.data.get(CONF_SOURCE_CONFIG_ENTRY_ID):
        if not (source_entry := hass.config_entries.async_get_entry(source_entry_id)):
            # Cleanup the orphaned entry using a call_soon to ensure
            # we can return before the entry is removed
            hass.loop.call_soon(
                hass_callback(
                    lambda: hass.async_create_task(
                        hass.config_entries.async_remove(entry.entry_id),
                        "remove orphaned bluetooth entry {entry.entry_id}",
                    )
                )
            )
            return True
        address = entry.unique_id
        assert address is not None
        source_domain = entry.data[CONF_SOURCE_DOMAIN]
        if mac_manufacturer := await get_manufacturer_from_mac(address):
            manufacturer = f"{mac_manufacturer} ({source_domain})"
        else:
            manufacturer = source_domain
        details = AdapterDetails(
            address=address,
            product=entry.data.get(CONF_SOURCE_MODEL),
            manufacturer=manufacturer,
        )
        await async_update_device(
            hass,
            entry,
            source_entry.title,
            details,
            entry.data.get(CONF_SOURCE_DEVICE_ID),
        )
        return True
    manager = _get_manager(hass)
    address = entry.unique_id
    assert address is not None
    adapter = await manager.async_get_adapter_from_address_or_recover(address)
    if adapter is None:
        raise ConfigEntryNotReady(
            f"Bluetooth adapter {adapter} with address {address} not found"
        )
    passive = entry.options.get(CONF_PASSIVE)
    adapters = await manager.async_get_bluetooth_adapters()
    mode = BluetoothScanningMode.PASSIVE if passive else BluetoothScanningMode.ACTIVE
    scanner = HaScanner(mode, adapter, address)
    scanner.async_setup()
    details = adapters[adapter]
    if entry.title == address:
        hass.config_entries.async_update_entry(
            entry, title=adapter_title(adapter, details)
        )
    slots: int = details.get(ADAPTER_CONNECTION_SLOTS) or DEFAULT_CONNECTION_SLOTS
    # Register the scanner before starting so
    # any raw advertisement data can be processed
    entry.async_on_unload(async_register_scanner(hass, scanner, connection_slots=slots))
    await async_update_device(hass, entry, adapter, details)
    try:
        await scanner.async_start()
    except (RuntimeError, ScannerStartError) as err:
        raise ConfigEntryNotReady(
            f"{adapter_human_name(adapter, address)}: {err}"
        ) from err
    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    entry.async_on_unload(scanner.async_stop)
    return True