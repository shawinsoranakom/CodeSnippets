async def ws_solar_forecast(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
    manager: EnergyManager,
) -> None:
    """Handle solar forecast command."""
    if manager.data is None:
        connection.send_result(msg["id"], {})
        return

    config_entries: dict[str, str | None] = {}

    for source in manager.data["energy_sources"]:
        if (
            source["type"] != "solar"
            or (solar_forecast := source.get("config_entry_solar_forecast")) is None
        ):
            continue

        for entry in solar_forecast:
            config_entries[entry] = None

    if not config_entries:
        connection.send_result(msg["id"], {})
        return

    forecasts: dict[str, SolarForecastType] = {}

    forecast_platforms = await async_get_energy_platforms(hass)

    for config_entry_id in config_entries:
        config_entry = hass.config_entries.async_get_entry(config_entry_id)
        # Filter out non-existing config entries or unsupported domains

        if config_entry is None or config_entry.domain not in forecast_platforms:
            continue

        forecast = await forecast_platforms[config_entry.domain](hass, config_entry_id)

        if forecast is not None:
            forecasts[config_entry_id] = forecast

    connection.send_result(msg["id"], forecasts)