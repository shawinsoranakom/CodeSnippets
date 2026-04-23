def _update_state(self, data):
        """Update the state of the entity."""
        if "pwr" in data:
            self._attr_is_on = bool(data["pwr"])

        if "brightness" in data:
            self._attr_brightness = round(data["brightness"] * 2.55)

        if self.supported_color_modes == {ColorMode.BRIGHTNESS}:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            return

        if {"hue", "saturation"}.issubset(data):
            self._attr_hs_color = [data["hue"], data["saturation"]]

        if "colortemp" in data:
            self._attr_color_temp_kelvin = data["colortemp"]

        if "bulb_colormode" in data:
            if data["bulb_colormode"] == BROADLINK_COLOR_MODE_RGB:
                self._attr_color_mode = ColorMode.HS
            elif data["bulb_colormode"] == BROADLINK_COLOR_MODE_WHITE:
                self._attr_color_mode = ColorMode.COLOR_TEMP
            else:
                # Scenes are not yet supported.
                self._attr_color_mode = ColorMode.UNKNOWN