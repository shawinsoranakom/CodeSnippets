def supported_color_modes(self) -> set[ColorMode]:
        """Get supported color modes."""
        color_mode = set()
        if (
            self._device.supports_color_temperature
            or self._device.supports_tunable_white
        ):
            color_mode.add(ColorMode.COLOR_TEMP)
        if self._device.supports_xyy_color:
            color_mode.add(ColorMode.XY)
        if self._device.supports_rgbw:
            color_mode.add(ColorMode.RGBW)
        elif self._device.supports_color:
            # one of RGB or RGBW so individual color configurations work properly
            color_mode.add(ColorMode.RGB)
        if self._device.supports_hs_color:
            color_mode.add(ColorMode.HS)
        if not color_mode:
            # brightness or on/off must be the only supported mode
            if self._device.supports_brightness:
                color_mode.add(ColorMode.BRIGHTNESS)
            else:
                color_mode.add(ColorMode.ONOFF)
        return color_mode