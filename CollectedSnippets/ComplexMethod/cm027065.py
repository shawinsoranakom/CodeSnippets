async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoFranceConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Meteo-France sensor platform."""
    coordinator_forecast = entry.runtime_data.forecast_coordinator
    coordinator_rain = entry.runtime_data.rain_coordinator
    coordinator_alert = entry.runtime_data.alert_coordinator

    entities: list[MeteoFranceSensor[Any]] = [
        MeteoFranceSensor(coordinator_forecast, description)
        for description in SENSOR_TYPES
    ]
    # Add rain forecast entity only if location support this feature
    if coordinator_rain:
        entities.extend(
            [
                MeteoFranceRainSensor(coordinator_rain, description)
                for description in SENSOR_TYPES_RAIN
            ]
        )
    # Add weather alert entity only if location support this feature
    if coordinator_alert:
        entities.extend(
            [
                MeteoFranceAlertSensor(coordinator_alert, description)
                for description in SENSOR_TYPES_ALERT
            ]
        )
    # Add weather probability entities only if location support this feature
    if coordinator_forecast.data.probability_forecast:
        entities.extend(
            [
                MeteoFranceSensor(coordinator_forecast, description)
                for description in SENSOR_TYPES_PROBABILITY
            ]
        )

    async_add_entities(entities, False)