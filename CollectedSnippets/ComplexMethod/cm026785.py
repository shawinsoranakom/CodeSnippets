async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        if brightness_supported(self.supported_color_modes):
            if ATTR_COLOR_TEMP_KELVIN in kwargs:
                await self._device.fade_to_color_temperature(
                    kwargs[ATTR_COLOR_TEMP_KELVIN]
                )
            if ATTR_RGB_COLOR in kwargs:
                await self._device.fade_to_rgbw_color(
                    tuple(color / 255 for color in kwargs[ATTR_RGB_COLOR])
                )
            if ATTR_RGBW_COLOR in kwargs:
                rgbw_color = tuple(color / 255 for color in kwargs[ATTR_RGBW_COLOR])
                await self._device.fade_to_rgbw_color(rgbw_color[:-1], rgbw_color[-1])
            if ATTR_BRIGHTNESS in kwargs or not self.is_on:
                await self._device.fade_to_brightness(
                    brightness_to_value(
                        self.BRIGHTNESS_SCALE,
                        kwargs.get(ATTR_BRIGHTNESS, self._last_brightness),
                    )
                )
        else:
            await self._device.switch_on()
        await self.coordinator.async_refresh()