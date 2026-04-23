def get_sensor_value(self, sensor_key: str) -> float | datetime | None:
        """Return the value of a sensor."""

        if self.data:
            value = self.data[sensor_key]

            if (sensor_key == SENSOR_REBOOT_TIME) and value:
                # convert the reboot time to a datetime object
                return utcnow() - timedelta(seconds=value)

            if (sensor_key == SENSOR_TEMPERATURE) and value:
                # convert the temperature value to a float
                return float(value)

            if (sensor_key == SENSOR_VOLTAGE) and value:
                # convert the voltage value to a float
                return float(value)

        return None