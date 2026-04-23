def _set_chars(self, char_values: dict[str, Any]) -> None:
        """Set characteristics based on the data coming from HomeKit."""
        _LOGGER.debug("HumidifierDehumidifier _set_chars: %s", char_values)

        if CHAR_TARGET_HUMIDIFIER_DEHUMIDIFIER in char_values:
            hk_value = char_values[CHAR_TARGET_HUMIDIFIER_DEHUMIDIFIER]
            if self._hk_device_class != hk_value:
                _LOGGER.error(
                    "%s is not supported", CHAR_TARGET_HUMIDIFIER_DEHUMIDIFIER
                )

        if CHAR_ACTIVE in char_values:
            self.async_call_service(
                HUMIDIFIER_DOMAIN,
                SERVICE_TURN_ON if char_values[CHAR_ACTIVE] else SERVICE_TURN_OFF,
                {ATTR_ENTITY_ID: self.entity_id},
                f"{CHAR_ACTIVE} to {char_values[CHAR_ACTIVE]}",
            )

        if self._target_humidity_char_name in char_values:
            state = self.hass.states.get(self.entity_id)
            assert state
            min_humidity, max_humidity = self.get_humidity_range(state)
            humidity = round(char_values[self._target_humidity_char_name])

            if (humidity < min_humidity) or (humidity > max_humidity):
                humidity = min(max_humidity, max(min_humidity, humidity))
                # Update the HomeKit value to the clamped humidity, so the user will get a visual feedback that they
                # cannot not set to a value below/above the min/max.
                self.char_target_humidity.set_value(humidity)

            self.async_call_service(
                HUMIDIFIER_DOMAIN,
                SERVICE_SET_HUMIDITY,
                {ATTR_ENTITY_ID: self.entity_id, ATTR_HUMIDITY: humidity},
                (
                    f"{self._target_humidity_char_name} to "
                    f"{char_values[self._target_humidity_char_name]}{PERCENTAGE}"
                ),
            )