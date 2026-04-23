async def _async_setup_rpc_entry(hass: HomeAssistant, entry: ShellyConfigEntry) -> bool:
    """Set up Shelly RPC based device from a config entry."""
    options = ConnectionOptions(
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD),
        device_mac=entry.unique_id,
        port=get_http_port(entry.data),
    )

    ws_context = await get_ws_context(hass)

    device = await RpcDevice.create(
        async_get_clientsession(hass),
        ws_context,
        options,
    )

    dev_reg = dr.async_get(hass)
    device_entry = None
    if entry.unique_id is not None:
        device_entry = dev_reg.async_get_device(
            connections={(CONNECTION_NETWORK_MAC, dr.format_mac(entry.unique_id))},
        )
    # https://github.com/home-assistant/core/pull/48076
    if device_entry and entry.entry_id not in device_entry.config_entries:
        LOGGER.debug("Detected first time setup for device %s", entry.title)
        device_entry = None

    sleep_period = entry.data.get(CONF_SLEEP_PERIOD)
    runtime_data = entry.runtime_data
    runtime_data.platforms = RPC_SLEEPING_PLATFORMS

    await er.async_migrate_entries(
        hass,
        entry.entry_id,
        async_migrate_rpc_sensor_description_unique_ids,
    )

    if sleep_period == 0:
        # Not a sleeping device, finish setup
        LOGGER.debug("Setting up online RPC device %s", entry.title)
        runtime_data.platforms = PLATFORMS
        try:
            await device.initialize()
            if not device.firmware_supported:
                async_create_issue_unsupported_firmware(hass, entry)
                await device.shutdown()
                raise ConfigEntryNotReady(
                    translation_domain=DOMAIN,
                    translation_key="firmware_unsupported",
                    translation_placeholders={"device": entry.title},
                )
            runtime_data.rpc_zigbee_firmware = device.zigbee_firmware
            runtime_data.rpc_supports_scripts = await device.supports_scripts()
            if runtime_data.rpc_supports_scripts:
                runtime_data.rpc_script_events = await get_rpc_scripts_event_types(
                    device, ignore_scripts=[BLE_SCRIPT_NAME]
                )
            remove_stale_blu_trv_devices(hass, device, entry)
        except (DeviceConnectionError, MacAddressMismatchError, RpcCallError) as err:
            await device.shutdown()
            raise ConfigEntryNotReady(
                translation_domain=DOMAIN,
                translation_key="device_communication_error",
                translation_placeholders={"device": entry.title},
            ) from err
        except InvalidAuthError as err:
            await device.shutdown()
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_error",
                translation_placeholders={"device": entry.title},
            ) from err

        await er.async_migrate_entries(
            hass,
            entry.entry_id,
            partial(async_migrate_rpc_virtual_components_unique_ids, device.config),
        )

        runtime_data.rpc = ShellyRpcCoordinator(hass, entry, device)
        runtime_data.rpc.async_setup()
        runtime_data.rpc_poll = ShellyRpcPollingCoordinator(hass, entry, device)
        await hass.config_entries.async_forward_entry_setups(
            entry, runtime_data.platforms
        )
        async_manage_deprecated_firmware_issue(hass, entry)
        async_manage_ble_scanner_firmware_unsupported_issue(
            hass,
            entry,
        )
        async_manage_outbound_websocket_incorrectly_enabled_issue(
            hass,
            entry,
        )
        async_manage_open_wifi_ap_issue(hass, entry)
        remove_empty_sub_devices(hass, entry)
    elif (
        sleep_period is None
        or device_entry is None
        or not er.async_entries_for_device(er.async_get(hass), device_entry.id)
    ):
        # Need to get sleep info or first time sleeping device setup, wait for device
        # If there are no entities for the device, it means we added the device, but
        # Home Assistant was restarted before the device was online. In this case we
        # cannot restore the entities, so we need to wait for the device to be online.
        LOGGER.debug(
            "Setup for device %s will resume when device is online", entry.title
        )
        runtime_data.rpc = ShellyRpcCoordinator(hass, entry, device)
        runtime_data.rpc.async_setup(runtime_data.platforms)
        # Try to connect to the device, if we reached here from config flow
        # and user woke up the device when adding it, we can continue setup
        # otherwise we will wait for the device to wake up
        if sleep_period:
            await runtime_data.rpc.async_device_online("setup")
    else:
        # Restore sensors for sleeping device
        LOGGER.debug("Setting up offline RPC device %s", entry.title)
        runtime_data.rpc = ShellyRpcCoordinator(hass, entry, device)
        runtime_data.rpc.async_setup()
        await hass.config_entries.async_forward_entry_setups(
            entry, runtime_data.platforms
        )

    ir.async_delete_issue(
        hass, DOMAIN, FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=entry.unique_id)
    )
    return True