def _new_sensor(sensor: EcoWittSensor) -> None:
        """Add new sensor."""
        if sensor.stype not in ECOWITT_SENSORS_MAPPING:
            return

        # Ignore metrics that are not supported by the user's locale
        if sensor.stype in _METRIC and hass.config.units is not METRIC_SYSTEM:
            return
        if sensor.stype in _IMPERIAL and hass.config.units is not US_CUSTOMARY_SYSTEM:
            return
        mapping = ECOWITT_SENSORS_MAPPING[sensor.stype]

        # Setup sensor description
        description = dataclasses.replace(
            mapping,
            key=sensor.key,
            name=sensor.name,
        )

        if sensor.stype in (
            EcoWittSensorTypes.RAIN_COUNT_INCHES,
            EcoWittSensorTypes.RAIN_COUNT_MM,
        ):
            if sensor.key not in _RAIN_COUNT_SENSORS_STATE_CLASS_MAPPING:
                _LOGGER.warning("Unknown rain count sensor: %s", sensor.key)
                return
            state_class = _RAIN_COUNT_SENSORS_STATE_CLASS_MAPPING[sensor.key]
            description = dataclasses.replace(description, state_class=state_class)

        async_add_entities([EcowittSensorEntity(sensor, description)])