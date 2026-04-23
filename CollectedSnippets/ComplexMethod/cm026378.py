def state_attributes(self) -> dict[str, Any]:
        """Return the optional state attributes."""
        supported_features = self.supported_features
        temperature_unit = self.temperature_unit
        precision = self.precision
        hass = self.hass

        data: dict[str, str | float | None] = {
            ATTR_CURRENT_TEMPERATURE: show_temp(
                hass, self.current_temperature, temperature_unit, precision
            ),
        }

        if ClimateEntityFeature.TARGET_TEMPERATURE in supported_features:
            data[ATTR_TEMPERATURE] = show_temp(
                hass,
                self.target_temperature,
                temperature_unit,
                precision,
            )

        if ClimateEntityFeature.TARGET_TEMPERATURE_RANGE in supported_features:
            data[ATTR_TARGET_TEMP_HIGH] = show_temp(
                hass, self.target_temperature_high, temperature_unit, precision
            )
            data[ATTR_TARGET_TEMP_LOW] = show_temp(
                hass, self.target_temperature_low, temperature_unit, precision
            )

        if (current_humidity := self.current_humidity) is not None:
            data[ATTR_CURRENT_HUMIDITY] = current_humidity

        if ClimateEntityFeature.TARGET_HUMIDITY in supported_features:
            data[ATTR_HUMIDITY] = self.target_humidity

        if ClimateEntityFeature.FAN_MODE in supported_features:
            data[ATTR_FAN_MODE] = self.fan_mode

        if hvac_action := self.hvac_action:
            data[ATTR_HVAC_ACTION] = hvac_action

        if ClimateEntityFeature.PRESET_MODE in supported_features:
            data[ATTR_PRESET_MODE] = self.preset_mode

        if ClimateEntityFeature.SWING_MODE in supported_features:
            data[ATTR_SWING_MODE] = self.swing_mode

        if ClimateEntityFeature.SWING_HORIZONTAL_MODE in supported_features:
            data[ATTR_SWING_HORIZONTAL_MODE] = self.swing_horizontal_mode

        return data