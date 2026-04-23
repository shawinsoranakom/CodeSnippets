def _async_update_attrs(self) -> None:
        """Handle updating _attr values."""
        state = self._device.state

        if (brightness := state.get_brightness()) is not None:
            self._attr_brightness = max(0, min(255, brightness))

        color_modes = self.supported_color_modes
        assert color_modes is not None

        if ColorMode.COLOR_TEMP in color_modes and (
            color_temp := state.get_colortemp()
        ):
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp_kelvin = color_temp
        elif (
            ColorMode.RGBWW in color_modes and (rgbww := state.get_rgbww()) is not None
        ):
            self._attr_color_mode = ColorMode.RGBWW
            self._attr_rgbww_color = rgbww
        elif ColorMode.RGBW in color_modes and (rgbw := state.get_rgbw()) is not None:
            self._attr_color_mode = ColorMode.RGBW
            self._attr_rgbw_color = rgbw

        self._attr_effect = effect = state.get_scene()
        if effect is not None:
            if brightness is not None:
                self._attr_color_mode = ColorMode.BRIGHTNESS
            else:
                self._attr_color_mode = ColorMode.ONOFF

        super()._async_update_attrs()