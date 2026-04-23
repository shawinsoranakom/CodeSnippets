async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the bulb on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS, self.brightness)
        hs_color = kwargs.get(ATTR_HS_COLOR, self.hs_color)
        attr_effect = cast(str, kwargs.get(ATTR_EFFECT, self.effect))

        if not self._tv.on:
            raise HomeAssistantError("TV is not available")

        effect = AmbilightEffect.from_str(attr_effect)

        if effect.style == "OFF":
            if self._last_selected_effect:
                effect = self._last_selected_effect
            else:
                effect = AmbilightEffect(EFFECT_AUTO, "FOLLOW_VIDEO", "STANDARD")

        if not effect.is_on(self._tv.powerstate):
            effect.mode = EFFECT_MODE
            effect.algorithm = None
            if self._tv.powerstate in ("On", None):
                effect.style = "internal"
            else:
                effect.style = "manual"

        if brightness is None:
            brightness = 255

        if hs_color is None:
            hs_color = (0, 0)

        if effect.mode == EFFECT_MODE:
            await self._set_ambilight_cached(effect, hs_color, brightness)
        elif effect.mode == EFFECT_AUTO:
            await self._set_ambilight_config(effect)
        elif effect.mode == EFFECT_EXPERT:
            await self._set_ambilight_expert_config(effect, hs_color, brightness)

        self._update_from_coordinator()
        self.async_write_ha_state()