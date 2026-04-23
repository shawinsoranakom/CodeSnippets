async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness: int = int((float(kwargs[ATTR_BRIGHTNESS]) / 255.0) * 100.0)
            await self.coordinator.set_brightness(self._device, brightness)

        if ATTR_RGB_COLOR in kwargs:
            self._attr_color_mode = ColorMode.RGB
            self._attr_effect = None
            self._last_color_state = None
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            await self.coordinator.set_rgb_color(self._device, red, green, blue)
        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_effect = None
            self._last_color_state = None
            temperature: float = kwargs[ATTR_COLOR_TEMP_KELVIN]
            await self.coordinator.set_temperature(self._device, int(temperature))
        elif ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if effect and self._attr_effect_list and effect in self._attr_effect_list:
                if effect == _NONE_SCENE:
                    self._attr_effect = None
                    await self._restore_last_color_state()
                else:
                    self._attr_effect = effect
                    self._save_last_color_state()
                    await self.coordinator.set_scene(self._device, effect)

        if not self.is_on or not kwargs:
            await self.coordinator.turn_on(self._device)

        self.async_write_ha_state()