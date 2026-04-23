async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        self._attr_is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]

        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]

        if ATTR_HS_COLOR in kwargs:
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = kwargs[ATTR_HS_COLOR]

        if ATTR_RGBW_COLOR in kwargs:
            self._attr_color_mode = ColorMode.RGBW
            self._attr_rgbw_color = kwargs[ATTR_RGBW_COLOR]

        if ATTR_RGBWW_COLOR in kwargs:
            self._attr_color_mode = ColorMode.RGBWW
            self._attr_rgbww_color = kwargs[ATTR_RGBWW_COLOR]

        if ATTR_WHITE in kwargs:
            self._attr_color_mode = ColorMode.WHITE
            self._attr_brightness = kwargs[ATTR_WHITE]

        # As we have disabled polling, we need to inform
        # Home Assistant about updates in our state ourselves.
        self.async_write_ha_state()