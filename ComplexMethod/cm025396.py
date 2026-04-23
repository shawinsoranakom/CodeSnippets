async def async_setup_entry(hass: HomeAssistant, entry: RitualsConfigEntry) -> bool:
    """Set up Rituals Perfume Genie from a config entry."""
    # Initiate reauth for old config entries which don't have username / password in the entry data
    if CONF_EMAIL not in entry.data or CONF_PASSWORD not in entry.data:
        raise ConfigEntryAuthFailed("Missing credentials")

    session = async_get_clientsession(hass)

    account = Account(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )

    try:
        # Authenticate first so API token/cookies are available for subsequent calls
        await account.authenticate()
        account_devices = await account.get_devices()

    except AuthenticationException as err:
        # Credentials invalid/expired -> raise AuthFailed to trigger reauth flow

        raise ConfigEntryAuthFailed(err) from err

    except ClientResponseError as err:
        _LOGGER.debug(
            "HTTP error during Rituals setup: status=%s, url=%s, headers=%s",
            err.status,
            err.request_info,
            dict(err.headers or {}),
        )
        raise ConfigEntryNotReady from err

    except ClientError as err:
        raise ConfigEntryNotReady from err

    # Migrate old unique_ids to the new format
    async_migrate_entities_unique_ids(hass, entry, account_devices)

    # The API provided by Rituals is currently rate limited to 30 requests
    # per hour per IP address. To avoid hitting this limit, we will adjust
    # the polling interval based on the number of diffusers one has.
    update_interval = UPDATE_INTERVAL * len(account_devices)

    # Create a coordinator for each diffuser
    coordinators = {
        diffuser.hublot: RitualsDataUpdateCoordinator(
            hass, entry, account, diffuser, update_interval
        )
        for diffuser in account_devices
    }

    # Refresh all coordinators
    await asyncio.gather(
        *[
            coordinator.async_config_entry_first_refresh()
            for coordinator in coordinators.values()
        ]
    )

    entry.runtime_data = coordinators
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True