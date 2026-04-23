def _set_chars(self, char_values: dict[str, Any]) -> None:
        _LOGGER.debug("Thermostat _set_chars: %s", char_values)
        events = []
        params: dict[str, Any] = {ATTR_ENTITY_ID: self.entity_id}
        service = None
        state = self.hass.states.get(self.entity_id)
        assert state
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        homekit_hvac_mode = _hk_hvac_mode_from_state(state)
        # Homekit will reset the mode when VIEWING the temp
        # Ignore it if its the same mode
        if (
            CHAR_TARGET_HEATING_COOLING in char_values
            and char_values[CHAR_TARGET_HEATING_COOLING] != homekit_hvac_mode
        ):
            target_hc = char_values[CHAR_TARGET_HEATING_COOLING]
            if target_hc not in self.hc_homekit_to_hass:
                # If the target heating cooling state we want does not
                # exist on the device, we have to sort it out
                # based on the current and target temperature since
                # siri will always send HC_HEAT_COOL_AUTO in this case
                # and hope for the best.
                hc_target_temp = char_values.get(CHAR_TARGET_TEMPERATURE)
                hc_current_temp = _get_current_temperature(state, self._unit)
                hc_fallback_order = HC_HEAT_COOL_PREFER_HEAT
                if (
                    hc_target_temp is not None
                    and hc_current_temp is not None
                    and hc_target_temp < hc_current_temp
                ):
                    hc_fallback_order = HC_HEAT_COOL_PREFER_COOL
                for hc_fallback in hc_fallback_order:
                    if hc_fallback in self.hc_homekit_to_hass:
                        _LOGGER.debug(
                            (
                                "Siri requested target mode: %s and the device does not"
                                " support, falling back to %s"
                            ),
                            target_hc,
                            hc_fallback,
                        )
                        self.char_target_heat_cool.value = target_hc = hc_fallback
                        break

            params[ATTR_HVAC_MODE] = self.hc_homekit_to_hass[target_hc]
            events.append(
                f"{CHAR_TARGET_HEATING_COOLING} to"
                f" {char_values[CHAR_TARGET_HEATING_COOLING]}"
            )
            # Many integrations do not actually implement `hvac_mode` for the
            # `SERVICE_SET_TEMPERATURE_THERMOSTAT` service so we made a call to
            # `SERVICE_SET_HVAC_MODE_THERMOSTAT` before calling `SERVICE_SET_TEMPERATURE_THERMOSTAT`
            # to ensure the device is in the right mode before setting the temp.
            self.async_call_service(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE_THERMOSTAT,
                params.copy(),
                ", ".join(events),
            )

        if CHAR_TARGET_TEMPERATURE in char_values:
            hc_target_temp = char_values[CHAR_TARGET_TEMPERATURE]
            if features & ClimateEntityFeature.TARGET_TEMPERATURE:
                service = SERVICE_SET_TEMPERATURE_THERMOSTAT
                temperature = self._temperature_to_states(hc_target_temp)
                events.append(
                    f"{CHAR_TARGET_TEMPERATURE} to"
                    f" {char_values[CHAR_TARGET_TEMPERATURE]}°C"
                )
                params[ATTR_TEMPERATURE] = temperature
            elif features & ClimateEntityFeature.TARGET_TEMPERATURE_RANGE:
                # Homekit will send us a target temperature
                # even if the device does not support it
                _LOGGER.debug(
                    "Homekit requested target temp: %s and the device does not support",
                    hc_target_temp,
                )
                if (
                    homekit_hvac_mode == HC_HEAT_COOL_HEAT
                    and CHAR_HEATING_THRESHOLD_TEMPERATURE not in char_values
                ):
                    char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE] = hc_target_temp
                if (
                    homekit_hvac_mode == HC_HEAT_COOL_COOL
                    and CHAR_COOLING_THRESHOLD_TEMPERATURE not in char_values
                ):
                    char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE] = hc_target_temp

        if (
            CHAR_HEATING_THRESHOLD_TEMPERATURE in char_values
            or CHAR_COOLING_THRESHOLD_TEMPERATURE in char_values
        ):
            assert self.char_cooling_thresh_temp
            assert self.char_heating_thresh_temp
            service = SERVICE_SET_TEMPERATURE_THERMOSTAT
            high = self.char_cooling_thresh_temp.value
            low = self.char_heating_thresh_temp.value
            min_temp, max_temp = self.get_temperature_range(state)
            if CHAR_COOLING_THRESHOLD_TEMPERATURE in char_values:
                events.append(
                    f"{CHAR_COOLING_THRESHOLD_TEMPERATURE} to"
                    f" {char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE]}°C"
                )
                high = char_values[CHAR_COOLING_THRESHOLD_TEMPERATURE]
                # If the device doesn't support TARGET_TEMPATURE
                # this can happen
                if high < low:
                    low = high - HEAT_COOL_DEADBAND
            if CHAR_HEATING_THRESHOLD_TEMPERATURE in char_values:
                events.append(
                    f"{CHAR_HEATING_THRESHOLD_TEMPERATURE} to"
                    f" {char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE]}°C"
                )
                low = char_values[CHAR_HEATING_THRESHOLD_TEMPERATURE]
                # If the device doesn't support TARGET_TEMPATURE
                # this can happen
                if low > high:
                    high = low + HEAT_COOL_DEADBAND

            high = min(high, max_temp)
            low = max(low, min_temp)

            params.update(
                {
                    ATTR_TARGET_TEMP_HIGH: self._temperature_to_states(high),
                    ATTR_TARGET_TEMP_LOW: self._temperature_to_states(low),
                }
            )

        if service:
            self.async_call_service(
                CLIMATE_DOMAIN,
                service,
                params,
                ", ".join(events),
            )

        if CHAR_TARGET_HUMIDITY in char_values:
            self.set_target_humidity(char_values[CHAR_TARGET_HUMIDITY])