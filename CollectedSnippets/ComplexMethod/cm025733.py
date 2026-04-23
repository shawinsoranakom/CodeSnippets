async def async_setup_entry(hass: HomeAssistant, entry: WeheatConfigEntry) -> bool:
    """Set up Weheat from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth2_implementation_unavailable",
        ) from err

    session = OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as ex:
        LOGGER.warning("API error: %s (%s)", ex.status, ex.message)
        if ex.status in (
            HTTPStatus.BAD_REQUEST,
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.FORBIDDEN,
        ):
            raise ConfigEntryAuthFailed("Token not valid, trigger renewal") from ex
        raise ConfigEntryNotReady from ex

    token = session.token[CONF_ACCESS_TOKEN]
    entry.runtime_data = []

    # fetch a list of the heat pumps the entry can access
    try:
        discovered_heat_pumps = await HeatPumpDiscovery.async_discover_active(
            API_URL, token, async_get_clientsession(hass)
        )
    except UnauthorizedException as error:
        raise ConfigEntryAuthFailed from error

    nr_of_pumps = len(discovered_heat_pumps)

    for pump_info in discovered_heat_pumps:
        LOGGER.debug("Adding %s", pump_info)
        # for each pump, add the coordinators

        new_heat_pump = HeatPumpInfo(pump_info)
        new_data_coordinator = WeheatDataUpdateCoordinator(
            hass, entry, session, pump_info, nr_of_pumps
        )
        new_energy_coordinator = WeheatEnergyUpdateCoordinator(
            hass, entry, session, pump_info
        )

        entry.runtime_data.append(
            WeheatData(
                heat_pump_info=new_heat_pump,
                data_coordinator=new_data_coordinator,
                energy_coordinator=new_energy_coordinator,
            )
        )

    await asyncio.gather(
        *[
            data.data_coordinator.async_config_entry_first_refresh()
            for data in entry.runtime_data
        ],
        *[
            data.energy_coordinator.async_config_entry_first_refresh()
            for data in entry.runtime_data
        ],
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True