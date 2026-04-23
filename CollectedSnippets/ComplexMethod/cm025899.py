def parse_data(self, data, raw_data):
        """Parse data sent by gateway."""
        if (value := data.get(self._data_key)) is None:
            return False
        if self._data_key in ("coordination", "status"):
            self._attr_native_value = value
            return True
        value = float(value)
        if self._data_key in ("temperature", "humidity", "pressure"):
            value /= 100
        elif self._data_key == "illumination":
            value = max(value - 300, 0)
        if self._data_key == "temperature" and (value < -50 or value > 60):
            return False
        if self._data_key == "humidity" and (value <= 0 or value > 100):
            return False
        if self._data_key == "pressure" and value == 0:
            return False
        if self._data_key in ("illumination", "lux"):
            self._attr_native_value = round(value)
        else:
            self._attr_native_value = round(value, 1)
        return True