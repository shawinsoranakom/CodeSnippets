def update_dynamic_attributes(self):
        """Update dynamic attributes of the luminary."""
        self._attr_is_on = self._luminary.on()
        self._attr_available = (
            self._luminary.reachable() and not self._luminary.deleted()
        )
        if brightness_supported(self._attr_supported_color_modes):
            self._attr_brightness = int(self._luminary.lum() * 2.55)

        if ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_temp_kelvin = self._luminary.temp() or DEFAULT_KELVIN

        if ColorMode.HS in self._attr_supported_color_modes:
            self._rgb_color = self._luminary.rgb()

        if len(self._attr_supported_color_modes) > 1:
            # The light supports hs + color temp, determine which one it is
            if self._rgb_color == (0, 0, 0):
                self._attr_color_mode = ColorMode.COLOR_TEMP
            else:
                self._attr_color_mode = ColorMode.HS