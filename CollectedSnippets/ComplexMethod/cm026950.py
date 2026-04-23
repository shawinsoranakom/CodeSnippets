def _calculate_color_values(self) -> None:
        """Calculate light colors."""
        (red_val, green_val, blue_val, ww_val, cw_val) = self._get_color_values()

        if self._current_color and isinstance(self._current_color.value, dict):
            multi_color = self._current_color.value
        else:
            multi_color = {}

        # Default: Brightness (no color) or Unknown
        if self.supported_color_modes == {ColorMode.BRIGHTNESS}:
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_color_mode = ColorMode.UNKNOWN

        # RGB support
        if red_val and green_val and blue_val:
            # prefer values from the multicolor property
            red = multi_color.get(COLOR_SWITCH_COMBINED_RED, red_val.value)
            green = multi_color.get(COLOR_SWITCH_COMBINED_GREEN, green_val.value)
            blue = multi_color.get(COLOR_SWITCH_COMBINED_BLUE, blue_val.value)
            if red is not None and green is not None and blue is not None:
                # convert to HS
                self._attr_hs_color = color_util.color_RGB_to_hs(red, green, blue)
                # Light supports color, set color mode to hs
                self._attr_color_mode = ColorMode.HS

        # color temperature support
        if ww_val and cw_val:
            warm_white = multi_color.get(COLOR_SWITCH_COMBINED_WARM_WHITE, ww_val.value)
            cold_white = multi_color.get(COLOR_SWITCH_COMBINED_COLD_WHITE, cw_val.value)
            # Calculate color temps based on whites
            if cold_white or warm_white:
                self._attr_color_temp_kelvin = (
                    color_util.color_temperature_mired_to_kelvin(
                        MAX_MIREDS
                        - ((cast(int, cold_white) / 255) * (MAX_MIREDS - MIN_MIREDS))
                    )
                )
                # White channels turned on, set color mode to color_temp
                self._attr_color_mode = ColorMode.COLOR_TEMP
            else:
                self._attr_color_temp_kelvin = None
        # only one white channel (warm white) = rgbw support
        elif red_val and green_val and blue_val and ww_val:
            white = multi_color.get(COLOR_SWITCH_COMBINED_WARM_WHITE, ww_val.value)
            if TYPE_CHECKING:
                assert (
                    red is not None
                    and green is not None
                    and blue is not None
                    and white is not None
                )
            self._attr_rgbw_color = (red, green, blue, white)
            # Light supports rgbw, set color mode to rgbw
            self._attr_color_mode = ColorMode.RGBW
        # only one white channel (cool white) = rgbw support
        elif cw_val:
            self._supports_rgbw = True
            white = multi_color.get(COLOR_SWITCH_COMBINED_COLD_WHITE, cw_val.value)
            if TYPE_CHECKING:
                assert (
                    red is not None
                    and green is not None
                    and blue is not None
                    and white is not None
                )
            self._attr_rgbw_color = (red, green, blue, white)
            # Light supports rgbw, set color mode to rgbw
            self._attr_color_mode = ColorMode.RGBW