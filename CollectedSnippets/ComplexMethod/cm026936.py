def set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        set_temp = True
        operation_mode: HVACMode | None = kwargs.get(ATTR_HVAC_MODE)
        temp_low: float | None = kwargs.get(ATTR_TARGET_TEMP_LOW)
        temp_high: float | None = kwargs.get(ATTR_TARGET_TEMP_HIGH)
        temperature: float | None = kwargs.get(ATTR_TEMPERATURE)

        client_mode = self._client.mode
        if (
            operation_mode
            and (new_mode := self._mode_map.get(operation_mode)) != client_mode
        ):
            set_temp = self._set_operation_mode(operation_mode)
            client_mode = new_mode

        if set_temp:
            if client_mode == self._client.MODE_HEAT:
                success = self._client.set_setpoints(temperature, self._client.cooltemp)
            elif client_mode == self._client.MODE_COOL:
                success = self._client.set_setpoints(self._client.heattemp, temperature)
            elif client_mode == self._client.MODE_AUTO:
                success = self._client.set_setpoints(temp_low, temp_high)
            else:
                success = False
                _LOGGER.error(
                    (
                        "The thermostat is currently not in a mode "
                        "that supports target temperature: %s"
                    ),
                    operation_mode,
                )

            if not success:
                _LOGGER.error("Failed to change the temperature")
        self.schedule_update_ha_state()