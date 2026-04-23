def discover_sensors(topic: str, payload: dict[str, Any]) -> list[ArwnSensor] | None:
    """Given a topic, dynamically create the right sensor type.

    Async friendly.
    """
    parts = topic.split("/")
    unit = payload.get("units", "")
    domain = parts[1]
    if domain == "temperature":
        name = parts[2]
        if unit == "F":
            unit = UnitOfTemperature.FAHRENHEIT
        else:
            unit = UnitOfTemperature.CELSIUS
        return [
            ArwnSensor(
                topic, name, "temp", unit, device_class=SensorDeviceClass.TEMPERATURE
            )
        ]
    if domain == "moisture":
        name = f"{parts[2]} Moisture"
        return [ArwnSensor(topic, name, "moisture", unit, "mdi:water-percent")]
    if domain == "rain":
        if len(parts) >= 3 and parts[2] == "today":
            return [
                ArwnSensor(
                    topic,
                    "Rain Since Midnight",
                    "since_midnight",
                    UnitOfPrecipitationDepth.INCHES,
                    device_class=SensorDeviceClass.PRECIPITATION,
                )
            ]
        return [
            ArwnSensor(
                topic + "/total",
                "Total Rainfall",
                "total",
                unit,
                device_class=SensorDeviceClass.PRECIPITATION,
            ),
            ArwnSensor(
                topic + "/rate",
                "Rainfall Rate",
                "rate",
                unit,
                device_class=SensorDeviceClass.PRECIPITATION,
            ),
        ]
    if domain == "barometer":
        return [
            ArwnSensor(topic, "Barometer", "pressure", unit, "mdi:thermometer-lines")
        ]
    if domain == "wind":
        return [
            ArwnSensor(
                topic + "/speed",
                "Wind Speed",
                "speed",
                unit,
                device_class=SensorDeviceClass.WIND_SPEED,
            ),
            ArwnSensor(
                topic + "/gust",
                "Wind Gust",
                "gust",
                unit,
                device_class=SensorDeviceClass.WIND_SPEED,
            ),
            ArwnSensor(
                topic + "/dir",
                "Wind Direction",
                "direction",
                DEGREE,
                "mdi:compass",
                device_class=SensorDeviceClass.WIND_DIRECTION,
                state_class=SensorStateClass.MEASUREMENT_ANGLE,
            ),
        ]
    return None