def parse_data(self, data, raw_data):
        """Parse data sent by gateway."""
        value = data.get(self._data_key)
        if value is None:
            return False

        if value == "long_click_press":
            self._attr_is_on = True
            click_type = "long_click_press"
        elif value == "long_click_release":
            self._attr_is_on = False
            click_type = "hold"
        elif value == "click":
            click_type = "single"
        elif value == "double_click":
            click_type = "double"
        elif value == "both_click":
            click_type = "both"
        elif value == "double_both_click":
            click_type = "double_both"
        elif value == "shake":
            click_type = "shake"
        elif value == "long_click":
            click_type = "long"
        elif value == "long_both_click":
            click_type = "long_both"
        else:
            _LOGGER.warning("Unsupported click_type detected: %s", value)
            return False

        self._hass.bus.async_fire(
            "xiaomi_aqara.click",
            {"entity_id": self.entity_id, "click_type": click_type},
        )
        self._last_action = click_type

        return True