async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        effect = kwargs.get(ATTR_EFFECT)

        if ATTR_HS_COLOR in kwargs:
            color_h, color_s = kwargs[ATTR_HS_COLOR]
        elif ATTR_BRIGHTNESS in kwargs:
            # Brightness update, keep color
            if self.hs_color is not None:
                color_h, color_s = self.hs_color
            else:
                color_h, color_s = 0, 0  # Back to white
        else:
            color_h, color_s = 0, 0  # Back to white

        try:
            if not self.is_on:
                await self._bulb.set_on()
            if brightness is not None:
                await self._bulb.set_color_hsv(
                    int(color_h), int(color_s), round(brightness * 100 / 255)
                )
            if effect == EFFECT_SUNRISE:
                await self._bulb.set_sunrise(30)
            if effect == EFFECT_RAINBOW:
                await self._bulb.set_rainbow(30)
        except MyStromConnectionError:
            _LOGGER.warning("No route to myStrom bulb")