async def async_setup_entry(hass: HomeAssistant, entry: LetPotConfigEntry) -> bool:
    """Set up LetPot from a config entry."""

    auth = AuthenticationInfo(
        access_token=entry.data[CONF_ACCESS_TOKEN],
        access_token_expires=entry.data[CONF_ACCESS_TOKEN_EXPIRES],
        refresh_token=entry.data[CONF_REFRESH_TOKEN],
        refresh_token_expires=entry.data[CONF_REFRESH_TOKEN_EXPIRES],
        user_id=entry.data[CONF_USER_ID],
        email=entry.data[CONF_EMAIL],
    )
    websession = async_get_clientsession(hass)
    client = LetPotClient(websession, auth)

    if not auth.is_valid:
        try:
            auth = await client.refresh_token()
            hass.config_entries.async_update_entry(
                entry,
                data={
                    CONF_ACCESS_TOKEN: auth.access_token,
                    CONF_ACCESS_TOKEN_EXPIRES: auth.access_token_expires,
                    CONF_REFRESH_TOKEN: auth.refresh_token,
                    CONF_REFRESH_TOKEN_EXPIRES: auth.refresh_token_expires,
                    CONF_USER_ID: auth.user_id,
                    CONF_EMAIL: auth.email,
                },
            )
        except LetPotAuthenticationException as exc:
            raise ConfigEntryAuthFailed from exc

    try:
        devices = await client.get_devices()
    except LetPotAuthenticationException as exc:
        raise ConfigEntryAuthFailed from exc
    except LetPotException as exc:
        raise ConfigEntryNotReady from exc

    device_client = LetPotDeviceClient(auth)

    coordinators: list[LetPotDeviceCoordinator] = [
        LetPotDeviceCoordinator(hass, entry, device, device_client)
        for device in devices
        if any(converter.supports_type(device.device_type) for converter in CONVERTERS)
    ]

    await asyncio.gather(
        *[
            coordinator.async_config_entry_first_refresh()
            for coordinator in coordinators
        ]
    )

    entry.runtime_data = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True