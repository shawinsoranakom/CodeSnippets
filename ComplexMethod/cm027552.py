async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the bulb on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        colortemp = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        rgb = kwargs.get(ATTR_RGB_COLOR)
        flash = kwargs.get(ATTR_FLASH)
        effect = kwargs.get(ATTR_EFFECT)

        duration = int(self.config[CONF_TRANSITION])  # in ms
        if ATTR_TRANSITION in kwargs:  # passed kwarg overrides config
            duration = int(kwargs[ATTR_TRANSITION] * 1000)  # kwarg in s

        if not self.is_on:
            await self._async_turn_on(duration)

        if self.config[CONF_MODE_MUSIC] and not self._bulb.music_mode:
            await self.async_set_music_mode(True)

        await self.async_set_hs(hs_color, duration)
        await self.async_set_rgb(rgb, duration)
        await self.async_set_colortemp(colortemp, duration)
        await self.async_set_brightness(brightness, duration)
        await self.async_set_flash(flash)
        await self.async_set_effect(effect)

        # save the current state if we had a manual change.
        if self.config[CONF_SAVE_ON_CHANGE] and (brightness or colortemp or rgb):
            await self.async_set_default()

        self._async_schedule_state_check(True)