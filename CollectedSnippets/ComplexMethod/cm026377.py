def capability_attributes(self) -> dict[str, Any] | None:
        """Return the capability attributes."""
        supported_features = self.supported_features
        temperature_unit = self.temperature_unit
        precision = self.precision
        hass = self.hass

        data: dict[str, Any] = {
            ATTR_HVAC_MODES: self.hvac_modes,
            ATTR_MIN_TEMP: show_temp(hass, self.min_temp, temperature_unit, precision),
            ATTR_MAX_TEMP: show_temp(hass, self.max_temp, temperature_unit, precision),
        }

        if target_temperature_step := self.target_temperature_step:
            data[ATTR_TARGET_TEMP_STEP] = target_temperature_step

        if ClimateEntityFeature.TARGET_HUMIDITY in supported_features:
            data[ATTR_MIN_HUMIDITY] = self.min_humidity
            data[ATTR_MAX_HUMIDITY] = self.max_humidity

            if self.target_humidity_step is not None:
                data[ATTR_TARGET_HUMIDITY_STEP] = self.target_humidity_step

        if ClimateEntityFeature.FAN_MODE in supported_features:
            data[ATTR_FAN_MODES] = self.fan_modes

        if ClimateEntityFeature.PRESET_MODE in supported_features:
            data[ATTR_PRESET_MODES] = self.preset_modes

        if ClimateEntityFeature.SWING_MODE in supported_features:
            data[ATTR_SWING_MODES] = self.swing_modes

        if ClimateEntityFeature.SWING_HORIZONTAL_MODE in supported_features:
            data[ATTR_SWING_HORIZONTAL_MODES] = self.swing_horizontal_modes

        return data