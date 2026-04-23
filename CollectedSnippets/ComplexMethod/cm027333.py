async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on.

        This method is a coroutine.
        """
        values: dict[str, Any] = {"state": True}
        if self._optimistic:
            self._attr_is_on = True

        if ATTR_BRIGHTNESS in kwargs:
            values["brightness"] = int(kwargs[ATTR_BRIGHTNESS])

            if self._optimistic:
                self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            values["color_temp"] = (
                kwargs[ATTR_COLOR_TEMP_KELVIN]
                if self._color_temp_kelvin
                else color_util.color_temperature_kelvin_to_mired(
                    kwargs[ATTR_COLOR_TEMP_KELVIN]
                )
            )

            if self._optimistic:
                self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
                self._attr_hs_color = None
                self._update_color_mode()

        if ATTR_HS_COLOR in kwargs:
            hs_color = kwargs[ATTR_HS_COLOR]

            # If there's a brightness topic set, we don't want to scale the RGB
            # values given using the brightness.
            if CONF_BRIGHTNESS_TEMPLATE in self._config:
                brightness = 255
            else:
                brightness = kwargs.get(
                    ATTR_BRIGHTNESS,
                    self._attr_brightness if self._attr_brightness is not None else 255,
                )
            rgb = color_util.color_hsv_to_RGB(
                hs_color[0], hs_color[1], brightness / 255 * 100
            )
            values["red"] = rgb[0]
            values["green"] = rgb[1]
            values["blue"] = rgb[2]
            values["hue"] = hs_color[0]
            values["sat"] = hs_color[1]

            if self._optimistic:
                self._attr_color_temp_kelvin = None
                self._attr_hs_color = kwargs[ATTR_HS_COLOR]
                self._update_color_mode()

        if ATTR_EFFECT in kwargs:
            values["effect"] = kwargs.get(ATTR_EFFECT)

            if self._optimistic:
                self._attr_effect = kwargs[ATTR_EFFECT]

        if ATTR_FLASH in kwargs:
            values["flash"] = kwargs.get(ATTR_FLASH)

        if ATTR_TRANSITION in kwargs:
            values["transition"] = kwargs[ATTR_TRANSITION]

        await self.async_publish_with_config(
            str(self._topics[CONF_COMMAND_TOPIC]),
            self._command_templates[CONF_COMMAND_ON_TEMPLATE](None, values),
        )

        if self._optimistic:
            self.async_write_ha_state()