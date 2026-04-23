def _update_status(self) -> None:
        """Update status itself."""
        super()._update_status()

        # Update fan, hvac and preset mode.
        if self.supported_features & ClimateEntityFeature.FAN_MODE:
            self._attr_fan_mode = STR_TO_HA_FAN.get(
                self.data.fan_mode, self.data.fan_mode
            )
        if self.supported_features & ClimateEntityFeature.SWING_MODE:
            self._attr_swing_mode = STR_TO_SWING.get(self.data.swing_mode)
        if self.supported_features & ClimateEntityFeature.SWING_HORIZONTAL_MODE:
            self._attr_swing_horizontal_mode = STR_TO_SWING.get(
                self.data.swing_horizontal_mode
            )

        if self.data.is_on:
            hvac_mode = self.data.hvac_mode
            if hvac_mode in STR_TO_HVAC:
                self._attr_hvac_mode = STR_TO_HVAC.get(hvac_mode)
                self._attr_preset_mode = PRESET_NONE
            elif hvac_mode in THINQ_PRESET_MODE:
                self._attr_hvac_mode = (
                    HVACMode.COOL if hvac_mode == "energy_saving" else HVACMode.FAN_ONLY
                )
                self._attr_preset_mode = hvac_mode
        else:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_preset_mode = PRESET_NONE

        self._attr_current_humidity = self.data.humidity
        self._attr_current_temperature = self.data.current_temp

        # Update min, max and step.
        if self.data.max is not None:
            self._attr_max_temp = self.data.max
        if self.data.min is not None:
            self._attr_min_temp = self.data.min

        self._attr_target_temperature_step = self.data.step

        # Update target temperatures.
        self._attr_target_temperature = self.data.target_temp
        self._attr_target_temperature_high = self.data.target_temp_high
        self._attr_target_temperature_low = self.data.target_temp_low

        # Update unit.
        self._attr_temperature_unit = (
            self._get_unit_of_measurement(self.data.unit) or UnitOfTemperature.CELSIUS
        )

        _LOGGER.debug(
            "[%s:%s] update status: c:%s, t:%s, l:%s, h:%s, hvac:%s, unit:%s, step:%s",
            self.coordinator.device_name,
            self.property_id,
            self.current_temperature,
            self.target_temperature,
            self.target_temperature_low,
            self.target_temperature_high,
            self.hvac_mode,
            self.temperature_unit,
            self.target_temperature_step,
        )