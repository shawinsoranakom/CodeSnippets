def query_attributes(self) -> dict[str, Any]:
        """Return the attributes of this trait for this entity."""
        device_class = self.state.attributes.get(ATTR_DEVICE_CLASS)

        def create_sensor_state(
            name: str, raw_value: float | None = None, current_state: str | None = None
        ) -> dict[str, Any]:
            sensor_state: dict[str, Any] = {
                "name": name,
                "rawValue": raw_value,
            }
            if current_state:
                sensor_state["currentSensorState"] = current_state
            return {"currentSensorStateData": [sensor_state]}

        if self.state.domain == sensor.DOMAIN:
            sensor_data = self.sensor_types.get(device_class)
            if device_class is None or sensor_data is None:
                return {}
            try:
                value = float(self.state.state)
            except ValueError:
                value = None
            if self.state.state == STATE_UNKNOWN:
                value = None
            current_state: str | None = None
            if device_class == sensor.SensorDeviceClass.AQI:
                current_state = self._air_quality_description_for_aqi(value)
            return create_sensor_state(sensor_data[0], value, current_state)

        binary_sensor_data = self.binary_sensor_types.get(device_class)
        if device_class is None or binary_sensor_data is None:
            return {}
        value = {
            STATE_ON: 0,
            STATE_OFF: 1,
            STATE_UNKNOWN: 2,
        }[self.state.state]
        return create_sensor_state(
            binary_sensor_data[0], current_state=binary_sensor_data[1][value]
        )