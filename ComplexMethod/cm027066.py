async def async_setup_entry(hass: HomeAssistant, entry: MeteoFranceConfigEntry) -> bool:
    """Set up a Meteo-France account from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = MeteoFranceClient()

    coordinator_forecast = MeteoFranceForecastUpdateCoordinator(hass, entry, client)
    coordinator_rain = None
    coordinator_alert = None

    # Fetch initial data so we have data when entities subscribe
    await coordinator_forecast.async_refresh()

    if not coordinator_forecast.last_update_success:
        raise ConfigEntryNotReady

    # Check rain forecast.
    coordinator_rain = MeteoFranceRainUpdateCoordinator(hass, entry, client)
    try:
        await coordinator_rain._async_refresh(log_failures=False)  # noqa: SLF001
    except RequestException:
        _LOGGER.warning(
            "1 hour rain forecast not available: %s is not in covered zone",
            entry.title,
        )

    department = coordinator_forecast.data.position.get("dept")
    _LOGGER.debug(
        "Department corresponding to %s is %s",
        entry.title,
        department,
    )
    if department is not None and is_valid_warning_department(department):
        if not hass.data[DOMAIN].get(department):
            coordinator_alert = MeteoFranceAlertUpdateCoordinator(
                hass,
                entry,
                client,
                department,
            )

            await coordinator_alert.async_refresh()

            if coordinator_alert.last_update_success:
                hass.data[DOMAIN][department] = True
        else:
            _LOGGER.warning(
                (
                    "Weather alert for department %s won't be added with city %s, as it"
                    " has already been added within another city"
                ),
                department,
                entry.title,
            )
    else:
        _LOGGER.warning(
            (
                "Weather alert not available: The city %s is not in metropolitan France"
                " or Andorre"
            ),
            entry.title,
        )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if coordinator_rain and not coordinator_rain.last_update_success:
        coordinator_rain = None
    if coordinator_alert and not coordinator_alert.last_update_success:
        coordinator_alert = None
    entry.runtime_data = MeteoFranceData(
        forecast_coordinator=coordinator_forecast,
        rain_coordinator=coordinator_rain,
        alert_coordinator=coordinator_alert,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True