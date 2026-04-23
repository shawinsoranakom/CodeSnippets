def _update_data(self) -> None:
        """Update data from device."""
        data = cast(SwitcherThermostat, self.coordinator.data)
        features = self._remote.modes_features[data.mode]

        # Ignore empty update from device that was power cycled
        if data.target_temperature == 0 and self.target_temperature is not None:
            return

        self._attr_current_temperature = data.temperature
        self._attr_target_temperature = float(data.target_temperature)

        self._attr_hvac_mode = HVACMode.OFF
        if data.device_state == DeviceState.ON:
            self._attr_hvac_mode = DEVICE_MODE_TO_HA[data.mode]

        self._attr_fan_mode = None
        self._attr_fan_modes = []
        if features["fan_levels"]:
            self._attr_fan_modes = [DEVICE_FAN_TO_HA[x] for x in features["fan_levels"]]
            self._attr_fan_mode = DEVICE_FAN_TO_HA[data.fan_level]

        self._attr_swing_mode = None
        self._attr_swing_modes = []
        if features["swing"]:
            self._attr_swing_mode = SWING_OFF
            self._attr_swing_modes = [SWING_VERTICAL, SWING_OFF]
            if data.swing == ThermostatSwing.ON:
                self._attr_swing_mode = SWING_VERTICAL