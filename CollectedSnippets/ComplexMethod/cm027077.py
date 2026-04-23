def process_service_info(
    hass: HomeAssistant,
    entry: BTHomeConfigEntry,
    device_registry: DeviceRegistry,
    service_info: BluetoothServiceInfoBleak,
) -> SensorUpdate:
    """Process a BluetoothServiceInfoBleak, running side effects and returning sensor data."""
    coordinator = entry.runtime_data
    data = coordinator.device_data
    issue_registry = ir.async_get(hass)
    issue_id = get_encryption_issue_id(entry.entry_id)
    update = data.update(service_info)

    # Block unencrypted payloads for devices that were previously verified as encrypted.
    if entry.data.get(CONF_BINDKEY) and data.downgrade_detected:
        if not coordinator.encryption_downgrade_logged:
            coordinator.encryption_downgrade_logged = True
            if not issue_registry.async_get_issue(DOMAIN, issue_id):
                _async_create_encryption_downgrade_issue(hass, entry, issue_id)
        return SensorUpdate(title=None, devices={})

    if data.bindkey_verified and (
        (existing_issue := issue_registry.async_get_issue(DOMAIN, issue_id))
        or coordinator.encryption_downgrade_logged
    ):
        coordinator.encryption_downgrade_logged = False
        if existing_issue:
            _async_clear_encryption_downgrade_issue(hass, entry, issue_id)

    discovered_event_classes = coordinator.discovered_event_classes
    if entry.data.get(CONF_SLEEPY_DEVICE, False) != data.sleepy_device:
        hass.config_entries.async_update_entry(
            entry,
            data=entry.data | {CONF_SLEEPY_DEVICE: data.sleepy_device},
        )
    if update.events:
        address = service_info.device.address
        for device_key, event in update.events.items():
            sensor_device_info = update.devices[device_key.device_id]
            device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                connections={(CONNECTION_BLUETOOTH, address)},
                identifiers={(BLUETOOTH_DOMAIN, address)},
                manufacturer=sensor_device_info.manufacturer,
                model=sensor_device_info.model,
                name=sensor_device_info.name,
                sw_version=sensor_device_info.sw_version,
                hw_version=sensor_device_info.hw_version,
            )
            # event_class may be postfixed with a number, ie 'button_2'
            # but if there is only one button then it will be 'button'
            event_class = event.device_key.key
            event_type = event.event_type

            ble_event = BTHomeBleEvent(
                device_id=device.id,
                address=address,
                event_class=event_class,  # ie 'button'
                event_type=event_type,  # ie 'press'
                event_properties=event.event_properties,
            )

            if event_class not in discovered_event_classes:
                discovered_event_classes.add(event_class)
                hass.config_entries.async_update_entry(
                    entry,
                    data=entry.data
                    | {CONF_DISCOVERED_EVENT_CLASSES: list(discovered_event_classes)},
                )
                async_dispatcher_send(
                    hass, format_discovered_event_class(address), event_class, ble_event
                )

            hass.bus.async_fire(BTHOME_BLE_EVENT, ble_event)
            async_dispatcher_send(
                hass,
                format_event_dispatcher_name(address, event_class),
                ble_event,
            )

    # If payload is encrypted and the bindkey is not verified then we need to reauth
    if data.encryption_scheme != EncryptionScheme.NONE and not data.bindkey_verified:
        entry.async_start_reauth(hass, data={"device": data})

    return update