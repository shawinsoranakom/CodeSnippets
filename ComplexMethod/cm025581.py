async def async_setup_entry(
    hass: HomeAssistant, config_entry: ReolinkConfigEntry
) -> bool:
    """Set up Reolink from a config entry."""
    host = ReolinkHost(hass, config_entry.data, config_entry.options, config_entry)

    try:
        await host.async_init()
    except (UserNotAdmin, CredentialsInvalidError, PasswordIncompatible) as err:
        await host.stop()
        raise ConfigEntryAuthFailed(err) from err
    except (
        ReolinkException,
        ReolinkError,
    ) as err:
        await host.stop()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_ready",
            translation_placeholders={"host": host.api.host, "err": str(err)},
        ) from err
    except BaseException:
        await host.stop()
        raise

    config_entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, host.stop)
    )

    # update the config info if needed for the next time
    if (
        host.api.port != config_entry.data[CONF_PORT]
        or host.api.use_https != config_entry.data[CONF_USE_HTTPS]
        or host.api.supported(None, "privacy_mode")
        != config_entry.data.get(CONF_SUPPORTS_PRIVACY_MODE)
        or host.api.baichuan.port != config_entry.data.get(CONF_BC_PORT)
        or host.api.baichuan_only != config_entry.data.get(CONF_BC_ONLY)
    ):
        if host.api.port != config_entry.data[CONF_PORT]:
            _LOGGER.warning(
                "HTTP(s) port of Reolink %s, changed from %s to %s",
                host.api.nvr_name,
                config_entry.data[CONF_PORT],
                host.api.port,
            )
        if (
            config_entry.data.get(CONF_BC_PORT, host.api.baichuan.port)
            != host.api.baichuan.port
        ):
            _LOGGER.warning(
                "Baichuan port of Reolink %s, changed from %s to %s",
                host.api.nvr_name,
                config_entry.data.get(CONF_BC_PORT),
                host.api.baichuan.port,
            )
        data = {
            **config_entry.data,
            CONF_PORT: host.api.port,
            CONF_USE_HTTPS: host.api.use_https,
            CONF_BC_PORT: host.api.baichuan.port,
            CONF_BC_ONLY: host.api.baichuan_only,
            CONF_SUPPORTS_PRIVACY_MODE: host.api.supported(None, "privacy_mode"),
        }
        hass.config_entries.async_update_entry(config_entry, data=data)

    min_timeout = host.api.timeout * (RETRY_ATTEMPTS + 2)

    device_coordinator = ReolinkDeviceCoordinator(
        hass,
        config_entry,
        host,
        min_timeout=min_timeout,
    )

    firmware_coordinator = ReolinkFirmwareCoordinator(
        hass,
        config_entry,
        host,
        min_timeout=min_timeout,
    )
    device_coordinator.firmware_coordinator = firmware_coordinator

    async def first_firmware_check(*args: Any) -> None:
        """Start first firmware check delayed to continue 24h schedule."""
        firmware_coordinator.update_interval = FIRMWARE_UPDATE_INTERVAL
        await firmware_coordinator.async_refresh()
        host.cancel_first_firmware_check = None

    # get update time from config entry
    check_time_sec = config_entry.data.get(CONF_FIRMWARE_CHECK_TIME)
    if check_time_sec is None:
        check_time_sec = uniform(0, 86400)
        data = {
            **config_entry.data,
            CONF_FIRMWARE_CHECK_TIME: check_time_sec,
        }
        hass.config_entries.async_update_entry(config_entry, data=data)

    # If camera WAN blocked, firmware check fails and takes long, do not prevent setup
    now = datetime.now(UTC)
    check_time = timedelta(seconds=check_time_sec)
    delta_midnight = now - now.replace(hour=0, minute=0, second=0, microsecond=0)
    firmware_check_delay = check_time - delta_midnight
    if firmware_check_delay < timedelta(0):
        firmware_check_delay += timedelta(days=1)
    _LOGGER.debug(
        "Scheduling first Reolink %s firmware check in %s",
        host.api.nvr_name,
        firmware_check_delay,
    )
    host.cancel_first_firmware_check = async_call_later(
        hass, firmware_check_delay, first_firmware_check
    )

    # Fetch initial data so we have data when entities subscribe
    try:
        await device_coordinator.async_config_entry_first_refresh()
    except BaseException:
        await host.stop()
        raise

    config_entry.runtime_data = ReolinkData(
        host=host,
        device_coordinator=device_coordinator,
        firmware_coordinator=firmware_coordinator,
    )

    migrate_entity_ids(hass, config_entry.entry_id, host)

    hass.http.register_view(PlaybackProxyView(hass))

    await register_callbacks(host, device_coordinator, hass)

    # ensure host device is setup before connected camera devices that use via_device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, host.unique_id)},
        connections={(dr.CONNECTION_NETWORK_MAC, host.api.mac_address)},
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True