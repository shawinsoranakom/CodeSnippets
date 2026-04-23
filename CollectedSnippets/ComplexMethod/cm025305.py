async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: GlancesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Glances sensors."""

    coordinator = config_entry.runtime_data
    entities: list[GlancesSensor] = []

    for sensor_type, sensors in coordinator.data.items():
        if sensor_type in ["fs", "diskio", "sensors", "raid", "gpu", "network"]:
            entities.extend(
                GlancesSensor(
                    coordinator,
                    sensor_description,
                    sensor_label,
                )
                for sensor_label, params in sensors.items()
                for param in params
                if (sensor_description := SENSOR_TYPES.get((sensor_type, param)))
            )
        else:
            entities.extend(
                GlancesSensor(
                    coordinator,
                    sensor_description,
                )
                for sensor in sensors
                if (sensor_description := SENSOR_TYPES.get((sensor_type, sensor)))
            )

    async_add_entities(entities)