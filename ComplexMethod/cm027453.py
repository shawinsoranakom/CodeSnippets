async def async_setup_entry(hass: HomeAssistant, entry: SynologyDSMConfigEntry) -> bool:
    """Set up Synology DSM sensors."""

    # Migrate device identifiers
    dev_reg = dr.async_get(hass)
    devices: list[dr.DeviceEntry] = dr.async_entries_for_config_entry(
        dev_reg, entry.entry_id
    )
    for device in devices:
        old_identifier = list(next(iter(device.identifiers)))
        if len(old_identifier) > 2:
            new_identifier = {
                (old_identifier.pop(0), "_".join([str(x) for x in old_identifier]))
            }
            _LOGGER.debug(
                "migrate identifier '%s' to '%s'", device.identifiers, new_identifier
            )
            dev_reg.async_update_device(device.id, new_identifiers=new_identifier)

    # Migrate existing entry configuration
    if entry.data.get(CONF_VERIFY_SSL) is None:
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_VERIFY_SSL: DEFAULT_VERIFY_SSL}
        )
    if CONF_BACKUP_SHARE not in entry.options:
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_BACKUP_SHARE: None, CONF_BACKUP_PATH: None},
        )
    if CONF_SCAN_INTERVAL in entry.options:
        current_options = {**entry.options}
        current_options.pop(CONF_SCAN_INTERVAL)
        hass.config_entries.async_update_entry(entry, options=current_options)

    # Continue setup
    api = SynoApi(hass, entry)
    try:
        await api.async_setup()
    except SYNOLOGY_AUTH_FAILED_EXCEPTIONS as err:
        raise_config_entry_auth_error(err)
    except (*SYNOLOGY_CONNECTION_EXCEPTIONS, SynologyDSMNotLoggedInException) as err:
        # SynologyDSMNotLoggedInException may be raised even if the user is
        # logged in because the session may have expired, and we need to retry
        # the login later.
        if err.args[0] and isinstance(err.args[0], dict):
            details = err.args[0].get(EXCEPTION_DETAILS, EXCEPTION_UNKNOWN)
        else:
            details = EXCEPTION_UNKNOWN
        raise ConfigEntryNotReady(details) from err

    # For SSDP compat
    if not entry.data.get(CONF_MAC):
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_MAC: api.dsm.network.macs}
        )

    coordinator_central = SynologyDSMCentralUpdateCoordinator(hass, entry, api)

    available_apis = api.dsm.apis

    coordinator_cameras: SynologyDSMCameraUpdateCoordinator | None = None
    if api.surveillance_station is not None:
        coordinator_cameras = SynologyDSMCameraUpdateCoordinator(hass, entry, api)
        await coordinator_cameras.async_config_entry_first_refresh()

    coordinator_switches: SynologyDSMSwitchUpdateCoordinator | None = None
    if (
        SynoSurveillanceStation.INFO_API_KEY in available_apis
        and SynoSurveillanceStation.HOME_MODE_API_KEY in available_apis
        and api.surveillance_station is not None
    ):
        coordinator_switches = SynologyDSMSwitchUpdateCoordinator(hass, entry, api)
        await coordinator_switches.async_config_entry_first_refresh()
        try:
            await coordinator_switches.async_setup()
        except SYNOLOGY_CONNECTION_EXCEPTIONS as ex:
            raise ConfigEntryNotReady from ex

    entry.runtime_data = SynologyDSMData(
        api=api,
        coordinator_central=coordinator_central,
        coordinator_central_old_update_success=True,
        coordinator_cameras=coordinator_cameras,
        coordinator_switches=coordinator_switches,
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if entry.options[CONF_BACKUP_SHARE]:

        def async_notify_backup_listeners() -> None:
            for listener in hass.data.get(DATA_BACKUP_AGENT_LISTENERS, []):
                listener()

        entry.async_on_unload(
            entry.async_on_state_change(async_notify_backup_listeners)
        )

        def async_check_last_update_success() -> None:
            if (
                last := coordinator_central.last_update_success
            ) is not entry.runtime_data.coordinator_central_old_update_success:
                entry.runtime_data.coordinator_central_old_update_success = last
                async_notify_backup_listeners()

        entry.runtime_data.coordinator_central.async_add_listener(
            async_check_last_update_success
        )

    return True