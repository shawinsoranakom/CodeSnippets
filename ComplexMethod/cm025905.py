def parse_data(self, data, raw_data):
        """Parse data sent by gateway."""
        if IN_USE in data:
            self._in_use = int(data[IN_USE])
            if not self._in_use:
                self._load_power = 0

        for key in (POWER_CONSUMED, ENERGY_CONSUMED):
            if key in data:
                self._power_consumed = round(float(data[key]), 2)
                break

        if LOAD_POWER in data:
            self._load_power = round(float(data[LOAD_POWER]), 2)

        value = data.get(self._data_key)
        if value not in ["on", "off"]:
            return False

        state = value == "on"
        if self._attr_is_on == state:
            return False
        self._attr_is_on = state
        return True