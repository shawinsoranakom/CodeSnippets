async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        supported_color_modes = self._attr_supported_color_modes

        attributes: dict[str, Any] = {}

        if ATTR_HS_COLOR in kwargs and ColorMode.HS in supported_color_modes:  # type: ignore[operator]
            hs_color = kwargs[ATTR_HS_COLOR]
            attributes["color_hs"] = [hs_color[0], hs_color[1]]

        if ATTR_WHITE in kwargs and ColorMode.WHITE in supported_color_modes:  # type: ignore[operator]
            attributes["white_value"] = scale_brightness(kwargs[ATTR_WHITE])

        if ATTR_TRANSITION in kwargs:
            attributes["transition"] = kwargs[ATTR_TRANSITION]

        if ATTR_BRIGHTNESS in kwargs and brightness_supported(supported_color_modes):
            attributes["brightness"] = scale_brightness(kwargs[ATTR_BRIGHTNESS])

        if (
            ATTR_COLOR_TEMP_KELVIN in kwargs
            and ColorMode.COLOR_TEMP in supported_color_modes  # type: ignore[operator]
        ):
            attributes["color_temp"] = color_util.color_temperature_kelvin_to_mired(
                kwargs[ATTR_COLOR_TEMP_KELVIN]
            )

        if ATTR_EFFECT in kwargs:
            attributes["effect"] = kwargs[ATTR_EFFECT]

        await self._tasmota_entity.set_state(True, attributes)