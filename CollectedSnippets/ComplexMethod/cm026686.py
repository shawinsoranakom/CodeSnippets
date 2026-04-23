def _update_attrs(self) -> None:
        """Update the attributes based on the current device state."""
        mode_data = self.device.modes[self.device.active_mode]
        mode = mode_data.name
        if mode == OpenRGBMode.OFF:
            mode = None
            mode_supports_colors = False
        else:
            mode_supports_colors = check_if_mode_supports_color(mode_data)

        color_mode = None
        rgb_color = None
        brightness = None
        on_by_color = True
        if mode_supports_colors:
            # Consider the first non-black LED color as the device color
            openrgb_off_color = RGBColor(*OFF_COLOR)
            openrgb_color = next(
                (color for color in self.device.colors if color != openrgb_off_color),
                openrgb_off_color,
            )

            if openrgb_color == openrgb_off_color:
                on_by_color = False
            else:
                rgb_color = (
                    openrgb_color.red,
                    openrgb_color.green,
                    openrgb_color.blue,
                )
                # Derive color and brightness from the scaled color
                hsv_color = color_RGB_to_hsv(*rgb_color)
                rgb_color = color_hs_to_RGB(hsv_color[0], hsv_color[1])
                brightness = round(255.0 * (hsv_color[2] / 100.0))

        elif mode is None:
            # If mode is Off, retain previous color mode to avoid changing the UI
            color_mode = self._attr_color_mode
        else:
            # If the current mode is not Off and does not support color, change to ON/OFF mode
            color_mode = ColorMode.ONOFF

        if not on_by_color:
            # If Off by color, retain previous color mode to avoid changing the UI
            color_mode = self._attr_color_mode

        if color_mode is None:
            # If color mode is still unknown, default to RGB
            color_mode = ColorMode.RGB

        if self._attr_brightness is not None and self._attr_brightness != brightness:
            self._previous_brightness = self._attr_brightness
        if self._attr_rgb_color is not None and self._attr_rgb_color != rgb_color:
            self._previous_rgb_color = self._attr_rgb_color
        if self._mode is not None and self._mode != mode:
            self._previous_mode = self._mode

        self._attr_color_mode = color_mode
        self._attr_supported_color_modes = {color_mode}
        self._attr_rgb_color = rgb_color
        self._attr_brightness = brightness
        if not self._supports_effects or mode is None:
            self._attr_effect = None
        elif mode in EFFECT_OFF_OPENRGB_MODES:
            self._attr_effect = EFFECT_OFF
        else:
            self._attr_effect = slugify(mode)
        self._mode = mode

        if mode is None:
            # If the mode is Off, the light is off
            self._attr_is_on = False
        else:
            self._attr_is_on = on_by_color