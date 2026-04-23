async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""

        rgbw = kwargs.get(ATTR_RGBW_COLOR)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        effect = kwargs.get(ATTR_EFFECT)
        color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        rgbww = kwargs.get(ATTR_RGBWW_COLOR)
        feature = self._feature
        value = feature.sensible_on_value
        rgb = kwargs.get(ATTR_RGB_COLOR)

        if rgbw is not None:
            value = list(rgbw)
        if color_temp_kelvin is not None:
            value = feature.return_color_temp_with_brightness(
                int(color_util.color_temperature_kelvin_to_mired(color_temp_kelvin)),
                self.brightness,
            )

        if rgbww is not None:
            value = list(rgbww)

        if rgb is not None:
            if self.color_mode == ColorMode.RGB and brightness is None:
                brightness = self.brightness
            value = list(rgb)

        if brightness is not None:
            if self.color_mode == ColorMode.COLOR_TEMP:
                value = feature.return_color_temp_with_brightness(
                    color_util.color_temperature_kelvin_to_mired(
                        self.color_temp_kelvin
                    ),
                    brightness,
                )
            else:
                value = feature.apply_brightness(value, brightness)

        try:
            await self._feature.async_on(value)
        except ValueError as exc:
            raise ValueError(
                f"Turning on '{self.name}' failed: Bad value {value}"
            ) from exc

        if effect is not None:
            try:
                effect_value = self.effect_list.index(effect)
                await self._feature.async_api_command("effect", effect_value)
            except ValueError as exc:
                raise ValueError(
                    f"Turning on with effect '{self.name}' failed: {effect} not in"
                    " effect list."
                ) from exc