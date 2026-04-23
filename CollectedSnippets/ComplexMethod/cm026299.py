async def async_setup_entry(hass: HomeAssistant, entry: UFPConfigEntry) -> bool:
    """Set up the UniFi Protect config entries."""

    protect = async_create_api_client(hass, entry)
    _LOGGER.debug("Connect to UniFi Protect")

    # Reuse ProtectData from previous retry or create new
    if hasattr(entry, "runtime_data"):
        data_service = entry.runtime_data
        data_service.api = protect
    else:
        data_service = ProtectData(hass, protect, SCAN_INTERVAL, entry)
        entry.runtime_data = data_service

    try:
        await protect.update()
    except NotAuthorized as err:
        data_service.auth_retries += 1
        if data_service.auth_retries > AUTH_RETRIES:
            raise ConfigEntryAuthFailed(err) from err
        raise ConfigEntryNotReady from err
    except (TimeoutError, ClientError, ServerDisconnectedError) as err:
        raise ConfigEntryNotReady from err
    bootstrap = protect.bootstrap
    nvr_info = bootstrap.nvr
    auth_user = bootstrap.users.get(bootstrap.auth_user_id)

    # Check if API key is missing
    if not protect.is_api_key_set() and auth_user and nvr_info.can_write(auth_user):
        try:
            new_api_key = await protect.create_api_key(
                name=f"Home Assistant ({hass.config.location_name})"
            )
        except (NotAuthorized, BadRequest) as err:
            _LOGGER.error("Failed to create API key: %s", err)
        else:
            protect.set_api_key(new_api_key)
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, CONF_API_KEY: new_api_key}
            )

    if not protect.is_api_key_set():
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="api_key_required",
        )

    if auth_user and auth_user.cloud_account:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "cloud_user",
            is_fixable=True,
            is_persistent=False,
            learn_more_url="https://www.home-assistant.io/integrations/unifiprotect/#local-user",
            severity=IssueSeverity.ERROR,
            translation_key="cloud_user",
            data={"entry_id": entry.entry_id},
        )

    if nvr_info.version < MIN_REQUIRED_PROTECT_V:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="protect_version",
            translation_placeholders={
                "current_version": str(nvr_info.version),
                "min_version": str(MIN_REQUIRED_PROTECT_V),
            },
        )

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=nvr_info.mac)

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, data_service.async_stop)
    )

    await _async_setup_entry(hass, entry, data_service, bootstrap)

    return True