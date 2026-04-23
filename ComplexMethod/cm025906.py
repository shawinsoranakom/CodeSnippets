async def async_setup_entry(hass: HomeAssistant, entry: RainbirdConfigEntry) -> bool:
    """Set up the config entry for Rain Bird."""

    clientsession = async_create_clientsession()
    _async_register_clientsession_shutdown(hass, entry, clientsession)

    try:
        async with asyncio.timeout(TIMEOUT_SECONDS):
            controller = await create_controller(
                clientsession,
                entry.data[CONF_HOST],
                entry.data[CONF_PASSWORD],
            )
    except TimeoutError as err:
        raise ConfigEntryNotReady from err
    except RainbirdAuthException as err:
        raise ConfigEntryAuthFailed from err
    except RainbirdApiException as err:
        raise ConfigEntryNotReady from err

    if not (await _async_fix_unique_id(hass, controller, entry)):
        return False
    if mac_address := entry.data.get(CONF_MAC):
        _async_fix_entity_unique_id(
            er.async_get(hass),
            entry.entry_id,
            format_mac(mac_address),
            str(entry.data[CONF_SERIAL_NUMBER]),
        )
        _async_fix_device_id(
            dr.async_get(hass),
            entry.entry_id,
            format_mac(mac_address),
            str(entry.data[CONF_SERIAL_NUMBER]),
        )

    try:
        model_info = await controller.get_model_and_version()
    except RainbirdAuthException as err:
        raise ConfigEntryAuthFailed from err
    except RainbirdApiException as err:
        raise ConfigEntryNotReady from err

    data = RainbirdData(
        controller,
        model_info,
        coordinator=RainbirdUpdateCoordinator(hass, entry, controller, model_info),
        schedule_coordinator=RainbirdScheduleUpdateCoordinator(hass, entry, controller),
    )
    await data.coordinator.async_config_entry_first_refresh()

    entry.runtime_data = data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True