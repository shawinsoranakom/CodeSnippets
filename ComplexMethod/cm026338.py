async def async_setup_entry(hass: HomeAssistant, entry: NASwebConfigEntry) -> bool:
    """Set up NASweb from a config entry."""

    if DATA_NASWEB not in hass.data:
        data = NASwebData()
        data.initialize(hass)
        hass.data[DATA_NASWEB] = data
    nasweb_data = hass.data[DATA_NASWEB]

    webio_api = WebioAPI(
        entry.data[CONF_HOST], entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )
    try:
        if not await webio_api.check_connection():
            raise ConfigEntryNotReady(
                f"[{entry.data[CONF_HOST]}] Check connection failed"
            )
        if not await webio_api.refresh_device_info():
            _LOGGER.error("[%s] Refresh device info failed", entry.data[CONF_HOST])
            raise ConfigEntryError(
                translation_key="config_entry_error_internal_error",
                translation_placeholders={"support_email": SUPPORT_EMAIL},
            )
        webio_serial = webio_api.get_serial_number()
        if webio_serial is None:
            _LOGGER.error("[%s] Serial number not available", entry.data[CONF_HOST])
            raise ConfigEntryError(
                translation_key="config_entry_error_internal_error",
                translation_placeholders={"support_email": SUPPORT_EMAIL},
            )
        if entry.unique_id != webio_serial:
            _LOGGER.error(
                "[%s] Serial number doesn't match config entry", entry.data[CONF_HOST]
            )
            raise ConfigEntryError(translation_key="config_entry_error_serial_mismatch")

        coordinator = NASwebCoordinator(
            hass, webio_api, name=f"NASweb[{webio_api.get_name()}]"
        )
        entry.runtime_data = coordinator
        nasweb_data.notify_coordinator.add_coordinator(webio_serial, entry.runtime_data)

        webhook_url = nasweb_data.get_webhook_url(hass)
        if not await webio_api.status_subscription(webhook_url, True):
            _LOGGER.error("Failed to subscribe for status updates from webio")
            raise ConfigEntryError(
                translation_key="config_entry_error_internal_error",
                translation_placeholders={"support_email": SUPPORT_EMAIL},
            )
        if not await nasweb_data.notify_coordinator.check_connection(webio_serial):
            _LOGGER.error("Did not receive status from device")
            raise ConfigEntryError(
                translation_key="config_entry_error_no_status_update",
                translation_placeholders={"support_email": SUPPORT_EMAIL},
            )
    except TimeoutError as error:
        raise ConfigEntryNotReady(
            f"[{entry.data[CONF_HOST]}] Check connection reached timeout"
        ) from error
    except AuthError as error:
        raise ConfigEntryError(
            translation_key="config_entry_error_invalid_authentication"
        ) from error
    except NoURLAvailableError as error:
        raise ConfigEntryError(
            translation_key="config_entry_error_missing_internal_url"
        ) from error

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, webio_serial)},
        manufacturer=MANUFACTURER,
        name=webio_api.get_name(),
        configuration_url=NASWEB_CONFIG_URL.format(host=entry.data[CONF_HOST]),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True