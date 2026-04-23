async def _async_setup_block_entry(
    hass: HomeAssistant, entry: ShellyConfigEntry
) -> bool:
    """Set up Shelly block based device from a config entry."""
    options = ConnectionOptions(
        entry.data[CONF_HOST],
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PASSWORD),
        device_mac=entry.unique_id,
    )

    coap_context = await get_coap_context(hass)

    device = await BlockDevice.create(
        async_get_clientsession(hass),
        coap_context,
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
    runtime_data.platforms = BLOCK_SLEEPING_PLATFORMS

    # Some old firmware have a wrong sleep period hardcoded value.
    # Following code block will force the right value for affected devices
    if (
        sleep_period == BLOCK_WRONG_SLEEP_PERIOD
        and entry.data[CONF_MODEL] in MODELS_WITH_WRONG_SLEEP_PERIOD
    ):
        LOGGER.warning(
            "Updating stored sleep period for %s: from %s to %s",
            entry.title,
            sleep_period,
            BLOCK_EXPECTED_SLEEP_PERIOD,
        )
        data = {**entry.data}
        data[CONF_SLEEP_PERIOD] = sleep_period = BLOCK_EXPECTED_SLEEP_PERIOD
        hass.config_entries.async_update_entry(entry, data=data)

    if sleep_period == 0:
        # Not a sleeping device, finish setup
        LOGGER.debug("Setting up online block device %s", entry.title)
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
        except (DeviceConnectionError, MacAddressMismatchError) as err:
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

        runtime_data.block = ShellyBlockCoordinator(hass, entry, device)
        runtime_data.block.async_setup()
        runtime_data.rest = ShellyRestCoordinator(hass, device, entry)
        await hass.config_entries.async_forward_entry_setups(
            entry, runtime_data.platforms
        )
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
        runtime_data.block = ShellyBlockCoordinator(hass, entry, device)
        runtime_data.block.async_setup(runtime_data.platforms)
    else:
        # Restore sensors for sleeping device
        LOGGER.debug("Setting up offline block device %s", entry.title)
        runtime_data.block = ShellyBlockCoordinator(hass, entry, device)
        runtime_data.block.async_setup()
        await hass.config_entries.async_forward_entry_setups(
            entry, runtime_data.platforms
        )

    ir.async_delete_issue(
        hass, DOMAIN, FIRMWARE_UNSUPPORTED_ISSUE_ID.format(unique=entry.unique_id)
    )
    return True