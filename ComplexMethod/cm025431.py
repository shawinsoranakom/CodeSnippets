async def async_setup_entry(
    hass: HomeAssistant,
    entry: WeatherFlowCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up WeatherFlow sensors based on a config entry."""

    coordinators = entry.runtime_data
    rest_coordinator = coordinators.rest
    wind_coordinator = coordinators.wind
    observation_coordinator = coordinators.observation

    entities: list[SensorEntity] = [
        WeatherFlowCloudSensorREST(rest_coordinator, sensor_description, station_id)
        for station_id in rest_coordinator.data
        for sensor_description in WF_SENSORS
    ]

    entities.extend(
        WeatherFlowWebsocketSensorWind(
            coordinator=wind_coordinator,
            description=sensor_description,
            station_id=station_id,
            device_id=device_id,
        )
        for station_id in wind_coordinator.stations.station_outdoor_device_map
        for device_id in wind_coordinator.stations.station_outdoor_device_map[
            station_id
        ]
        for sensor_description in WEBSOCKET_WIND_SENSORS
    )

    entities.extend(
        WeatherFlowWebsocketSensorObservation(
            coordinator=observation_coordinator,
            description=sensor_description,
            station_id=station_id,
            device_id=device_id,
        )
        for station_id in observation_coordinator.stations.station_outdoor_device_map
        for device_id in observation_coordinator.stations.station_outdoor_device_map[
            station_id
        ]
        for sensor_description in WEBSOCKET_OBSERVATION_SENSORS
    )
    async_add_entities(entities)