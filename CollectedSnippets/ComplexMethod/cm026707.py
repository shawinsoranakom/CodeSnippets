async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        effect = kwargs.get(ATTR_EFFECT)
        transition = kwargs.get(ATTR_TRANSITION)

        if effect:
            if effect not in self.effect_list:
                raise ValueError(
                    f"Attempting to apply effect not in the effect list: '{effect}'"
                )
            await self._nanoleaf.set_effect(effect)
        elif hs_color:
            hue, saturation = hs_color
            await self._nanoleaf.set_hue(int(hue))
            await self._nanoleaf.set_saturation(int(saturation))
        elif color_temp_kelvin:
            await self._nanoleaf.set_color_temperature(color_temp_kelvin)
        if transition:
            if brightness:  # tune to the required brightness in n seconds
                await self._nanoleaf.set_brightness(
                    int(brightness / 2.55), transition=int(kwargs[ATTR_TRANSITION])
                )
            else:  # If brightness is not specified, assume full brightness
                await self._nanoleaf.set_brightness(100, transition=int(transition))
        else:  # If no transition is occurring, turn on the light
            await self._nanoleaf.turn_on()
            if brightness:
                await self._nanoleaf.set_brightness(int(brightness / 2.55))
        await self.coordinator.async_refresh()