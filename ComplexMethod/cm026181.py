def _update_state(self):
        """Update the state of the class based sensor data."""
        result = []
        for sensor_name in self._sensormap.values():
            params = self.READINGS[sensor_name]
            if (value := getattr(self, f"_{sensor_name}")) is not None:
                if value == STATE_UNAVAILABLE:
                    result.append(f"{sensor_name} unavailable")
                else:
                    if sensor_name == READING_BRIGHTNESS:
                        result.append(
                            self._check_min(
                                sensor_name, self._brightness_history.max, params
                            )
                        )
                    else:
                        result.append(self._check_min(sensor_name, value, params))
                    result.append(self._check_max(sensor_name, value, params))

        result = [r for r in result if r is not None]

        if result:
            self._state = STATE_PROBLEM
            self._problems = ", ".join(result)
        else:
            self._state = STATE_OK
            self._problems = PROBLEM_NONE
        _LOGGER.debug("New data processed")
        self.async_write_ha_state()