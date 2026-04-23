def remove_stale_blu_trv_devices(
    hass: HomeAssistant, rpc_device: RpcDevice, entry: ConfigEntry
) -> None:
    """Remove stale BLU TRV devices."""
    if rpc_device.model != MODEL_BLU_GATEWAY_G3:
        return

    dev_reg = dr.async_get(hass)
    devices = dev_reg.devices.get_devices_for_config_entry_id(entry.entry_id)
    config = rpc_device.config
    blutrv_keys = get_rpc_key_ids(config, BLU_TRV_IDENTIFIER)
    trv_addrs = [config[f"{BLU_TRV_IDENTIFIER}:{key}"]["addr"] for key in blutrv_keys]

    for device in devices:
        if not device.via_device_id:
            # Device is not a sub-device, skip
            continue

        if any(
            identifier[0] == DOMAIN and identifier[1] in trv_addrs
            for identifier in device.identifiers
        ):
            continue

        LOGGER.debug("Removing stale BLU TRV device %s", device.name)
        dev_reg.async_update_device(device.id, remove_config_entry_id=entry.entry_id)