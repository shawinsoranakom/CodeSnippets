async def _async_set_mode(self, **kwargs: Any) -> None:
        """Set an effect or color mode."""
        brightness = self._async_brightness(**kwargs)
        # Handle switch to Effect Mode
        if effect := kwargs.get(ATTR_EFFECT):
            await self._async_set_effect(effect, brightness)
            return
        # Handle switch to CCT Color Mode
        if color_temp_kelvin := kwargs.get(ATTR_COLOR_TEMP_KELVIN):
            if (
                ATTR_BRIGHTNESS not in kwargs
                and self.color_mode in MULTI_BRIGHTNESS_COLOR_MODES
            ):
                # When switching to color temp from RGBWW or RGB&W mode,
                # we do not want the overall brightness of the RGB channels
                brightness = max(MIN_CCT_BRIGHTNESS, *self._device.rgb)
            await self._device.async_set_white_temp(color_temp_kelvin, brightness)
            return
        # Handle switch to RGB Color Mode
        if rgb := kwargs.get(ATTR_RGB_COLOR):
            if not self._device.requires_turn_on:
                rgb = _min_rgb_brightness(rgb)
            red, green, blue = rgb
            await self._device.async_set_levels(red, green, blue, brightness=brightness)
            return
        # Handle switch to RGBW Color Mode
        if rgbw := kwargs.get(ATTR_RGBW_COLOR):
            if ATTR_BRIGHTNESS in kwargs:
                rgbw = rgbw_brightness(rgbw, brightness)
            rgbw = _min_rgbw_brightness(rgbw, self._device.rgbw)
            await self._device.async_set_levels(*rgbw)
            return
        # Handle switch to RGBWW Color Mode
        if rgbcw := kwargs.get(ATTR_RGBWW_COLOR):
            if ATTR_BRIGHTNESS in kwargs:
                rgbcw = rgbcw_brightness(kwargs[ATTR_RGBWW_COLOR], brightness)
            rgbwc = rgbcw_to_rgbwc(rgbcw)
            rgbwc = _min_rgbwc_brightness(rgbwc, self._device.rgbww)
            await self._device.async_set_levels(*rgbwc)
            return
        if (white := kwargs.get(ATTR_WHITE)) is not None:
            await self._device.async_set_levels(w=white)
            return