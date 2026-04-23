def state_changed(self, entity_id: str, new_state: State | None) -> None:
        """Update the sensor status."""
        if new_state is None:
            return
        value: str | float
        value = new_state.state
        _LOGGER.debug("Received callback from %s with value %s", entity_id, value)
        if value == STATE_UNKNOWN:
            return

        reading = self._sensormap[entity_id]
        if reading == READING_MOISTURE:
            if value != STATE_UNAVAILABLE:
                value = int(float(value))
            self._moisture = value
        elif reading == READING_BATTERY:
            if value != STATE_UNAVAILABLE:
                value = int(float(value))
            self._battery = value
        elif reading == READING_TEMPERATURE:
            if value != STATE_UNAVAILABLE:
                value = float(value)
            self._temperature = value
        elif reading == READING_CONDUCTIVITY:
            if value != STATE_UNAVAILABLE:
                value = int(float(value))
            self._conductivity = value
        elif reading == READING_BRIGHTNESS:
            if value != STATE_UNAVAILABLE:
                value = int(float(value))
            self._brightness = value
            self._brightness_history.add_measurement(
                self._brightness, new_state.last_updated
            )
        else:
            raise HomeAssistantError(
                f"Unknown reading from sensor {entity_id}: {value}"
            )
        if ATTR_UNIT_OF_MEASUREMENT in new_state.attributes:
            self._unit_of_measurement[reading] = new_state.attributes.get(
                ATTR_UNIT_OF_MEASUREMENT
            )
        self._update_state()