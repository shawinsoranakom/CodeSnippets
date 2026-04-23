def async_update_state(self, new_state: State) -> None:
        """Update state without rechecking the device features."""
        attributes = new_state.attributes
        features = attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        # Update target operation mode FIRST
        if (homekit_hvac_mode := _hk_hvac_mode_from_state(new_state)) is not None:
            if homekit_hvac_mode in self.hc_homekit_to_hass:
                self.char_target_heat_cool.set_value(homekit_hvac_mode)
            else:
                _LOGGER.error(
                    (
                        "Cannot map hvac target mode: %s to homekit as only %s modes"
                        " are supported"
                    ),
                    new_state.state,
                    self.hc_homekit_to_hass,
                )

        # Set current operation mode for supported thermostats
        if hvac_action := attributes.get(ATTR_HVAC_ACTION):
            self.char_current_heat_cool.set_value(
                HC_HASS_TO_HOMEKIT_ACTION.get(hvac_action, HC_HEAT_COOL_OFF)
            )

        # Update current temperature
        current_temp = _get_current_temperature(new_state, self._unit)
        if current_temp is not None:
            self.char_current_temp.set_value(current_temp)

        # Update current humidity
        if CHAR_CURRENT_HUMIDITY in self.chars:
            assert self.char_current_humidity
            current_humdity = attributes.get(ATTR_CURRENT_HUMIDITY)
            if isinstance(current_humdity, (int, float)):
                self.char_current_humidity.set_value(current_humdity)

        # Update target humidity
        if CHAR_TARGET_HUMIDITY in self.chars:
            assert self.char_target_humidity
            target_humdity = attributes.get(ATTR_HUMIDITY)
            if isinstance(target_humdity, (int, float)):
                self.char_target_humidity.set_value(target_humdity)

        # Update cooling threshold temperature if characteristic exists
        if self.char_cooling_thresh_temp:
            cooling_thresh = attributes.get(ATTR_TARGET_TEMP_HIGH)
            if isinstance(cooling_thresh, (int, float)):
                cooling_thresh = self._temperature_to_homekit(cooling_thresh)
                self.char_cooling_thresh_temp.set_value(cooling_thresh)

        # Update heating threshold temperature if characteristic exists
        if self.char_heating_thresh_temp:
            heating_thresh = attributes.get(ATTR_TARGET_TEMP_LOW)
            if isinstance(heating_thresh, (int, float)):
                heating_thresh = self._temperature_to_homekit(heating_thresh)
                self.char_heating_thresh_temp.set_value(heating_thresh)

        # Update target temperature
        target_temp = _get_target_temperature(new_state, self._unit)
        if (
            target_temp is None
            and features & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        ):
            # Homekit expects a target temperature
            # even if the device does not support it
            hc_hvac_mode = self.char_target_heat_cool.value
            if hc_hvac_mode == HC_HEAT_COOL_HEAT:
                temp_low = attributes.get(ATTR_TARGET_TEMP_LOW)
                if isinstance(temp_low, (int, float)):
                    target_temp = self._temperature_to_homekit(temp_low)
            elif hc_hvac_mode == HC_HEAT_COOL_COOL:
                temp_high = attributes.get(ATTR_TARGET_TEMP_HIGH)
                if isinstance(temp_high, (int, float)):
                    target_temp = self._temperature_to_homekit(temp_high)
        if target_temp:
            self.char_target_temp.set_value(target_temp)

        # Update display units
        if self._unit and self._unit in UNIT_HASS_TO_HOMEKIT:
            unit = UNIT_HASS_TO_HOMEKIT[self._unit]
            self.char_display_units.set_value(unit)

        if self.fan_chars:
            self._async_update_fan_state(new_state)