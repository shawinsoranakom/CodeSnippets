def _async_send_events(self, _now: datetime) -> None:
        """Process all changes at once."""
        _LOGGER.debug("Coalesced _set_chars: %s", self._pending_events)
        char_values = self._pending_events
        self._pending_events = {}
        events = []
        service = SERVICE_TURN_ON
        params: dict[str, Any] = {ATTR_ENTITY_ID: self.entity_id}
        has_on = CHAR_ON in char_values

        if has_on:
            if not char_values[CHAR_ON]:
                service = SERVICE_TURN_OFF
            events.append(f"Set state to {char_values[CHAR_ON]}")

        brightness_pct = None
        if CHAR_BRIGHTNESS in char_values:
            if char_values[CHAR_BRIGHTNESS] == 0:
                if has_on:
                    events[-1] = "Set state to 0"
                else:
                    events.append("Set state to 0")
                service = SERVICE_TURN_OFF
            else:
                brightness_pct = char_values[CHAR_BRIGHTNESS]
            events.append(f"brightness at {char_values[CHAR_BRIGHTNESS]}%")

        if service == SERVICE_TURN_OFF:
            self.async_call_service(
                LIGHT_DOMAIN,
                service,
                {ATTR_ENTITY_ID: self.entity_id},
                ", ".join(events),
            )
            return

        # Handle white channels
        if CHAR_COLOR_TEMPERATURE in char_values:
            temp = char_values[CHAR_COLOR_TEMPERATURE]
            events.append(f"color temperature at {temp}")
            bright_val = round(
                ((brightness_pct or self.char_brightness.value) * 255) / 100
            )
            if self.color_temp_supported:
                params[ATTR_COLOR_TEMP_KELVIN] = color_temperature_mired_to_kelvin(temp)
            elif self.rgbww_supported:
                params[ATTR_RGBWW_COLOR] = color_temperature_to_rgbww(
                    color_temperature_mired_to_kelvin(temp),
                    bright_val,
                    color_temperature_mired_to_kelvin(self.max_mireds),
                    color_temperature_mired_to_kelvin(self.min_mireds),
                )
            elif self.rgbw_supported:
                params[ATTR_RGBW_COLOR] = (*(0,) * 3, bright_val)
            elif self.white_supported:
                params[ATTR_WHITE] = bright_val

        elif CHAR_HUE in char_values or CHAR_SATURATION in char_values:
            hue_sat = (
                char_values.get(CHAR_HUE, self.char_hue.value),
                char_values.get(CHAR_SATURATION, self.char_saturation.value),
            )
            _LOGGER.debug("%s: Set hs_color to %s", self.entity_id, hue_sat)
            events.append(f"set color at {hue_sat}")
            params[ATTR_HS_COLOR] = hue_sat

        if (
            brightness_pct
            and ATTR_RGBWW_COLOR not in params
            and ATTR_RGBW_COLOR not in params
        ):
            params[ATTR_BRIGHTNESS_PCT] = brightness_pct

        _LOGGER.debug(
            "Calling light service with params: %s -> %s", char_values, params
        )
        self.async_call_service(LIGHT_DOMAIN, service, params, ", ".join(events))