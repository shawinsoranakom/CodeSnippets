async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness, transition = self._async_extract_brightness_transition(**kwargs)
        effect_off_called = False
        if effect := kwargs.get(ATTR_EFFECT):
            if effect in {LightEffect.LIGHT_EFFECTS_OFF, EFFECT_OFF}:
                if self._effect_module.effect is not LightEffect.LIGHT_EFFECTS_OFF:
                    await self._effect_module.set_effect(LightEffect.LIGHT_EFFECTS_OFF)
                    effect_off_called = True
                if len(kwargs) == 1:
                    return
            elif effect in self._effect_module.effect_list:
                await self._effect_module.set_effect(
                    kwargs[ATTR_EFFECT], brightness=brightness, transition=transition
                )
                return
            else:
                _LOGGER.error("Invalid effect %s for %s", effect, self._device.host)
                return

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            if self.effect and self.effect != EFFECT_OFF and not effect_off_called:
                # If there is an effect in progress
                # we have to clear the effect
                # before we can set a color temp
                await self._effect_module.set_effect(LightEffect.LIGHT_EFFECTS_OFF)
            await self._async_set_color_temp(
                kwargs[ATTR_COLOR_TEMP_KELVIN], brightness, transition
            )
        elif ATTR_HS_COLOR in kwargs:
            await self._async_set_hsv(kwargs[ATTR_HS_COLOR], brightness, transition)
        else:
            await self._async_turn_on_with_brightness(brightness, transition)