async def async_get_device_config(hass, config_entry):
    """Initiate the connection and services."""
    # Make a copy of addresses due to edge case where the list of devices could
    # change during status update
    # Cannot be done concurrently due to issues with the underlying protocol.
    for address in list(devices):
        if devices[address].is_battery:
            continue
        with suppress(AttributeError):
            await devices[address].async_status()

    load_aldb = 2 if devices.modem.aldb.read_write_mode == ReadWriteMode.UNKNOWN else 1
    await devices.async_load(id_devices=1, load_modem_aldb=load_aldb)
    for addr in list(devices):
        device = devices[addr]
        flags = True
        for name in device.operating_flags:
            if not device.operating_flags[name].is_loaded:
                flags = False
                break
        if flags:
            for name in device.properties:
                if not device.properties[name].is_loaded:
                    flags = False
                    break

        # Cannot be done concurrently due to issues with the underlying protocol.
        if not device.aldb.is_loaded or not flags:
            await device.async_read_config()

    await devices.async_save(workdir=hass.config.config_dir)