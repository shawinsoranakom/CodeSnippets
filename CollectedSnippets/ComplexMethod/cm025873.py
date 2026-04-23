async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        data: SetStateAttributes = {"on": True}

        if ATTR_BRIGHTNESS in kwargs:
            data["brightness"] = kwargs[ATTR_BRIGHTNESS]

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            data["color_temperature"] = color_temperature_kelvin_to_mired(
                kwargs[ATTR_COLOR_TEMP_KELVIN]
            )

        if ATTR_HS_COLOR in kwargs:
            if ColorMode.XY in self._attr_supported_color_modes:
                data["xy"] = color_hs_to_xy(*kwargs[ATTR_HS_COLOR])
            else:
                data["hue"] = int(kwargs[ATTR_HS_COLOR][0] / 360 * 65535)
                data["saturation"] = int(kwargs[ATTR_HS_COLOR][1] / 100 * 255)

        if ATTR_XY_COLOR in kwargs:
            data["xy"] = kwargs[ATTR_XY_COLOR]

        if ATTR_TRANSITION in kwargs:
            data["transition_time"] = int(kwargs[ATTR_TRANSITION] * 10)
        elif "IKEA" in self._device.manufacturer:
            data["transition_time"] = 0

        if ATTR_FLASH in kwargs and kwargs[ATTR_FLASH] in FLASH_TO_DECONZ:
            data["alert"] = FLASH_TO_DECONZ[kwargs[ATTR_FLASH]]
            del data["on"]

        if ATTR_EFFECT in kwargs and kwargs[ATTR_EFFECT] in EFFECT_TO_DECONZ:
            data["effect"] = EFFECT_TO_DECONZ[kwargs[ATTR_EFFECT]]

        await self.api.set_state(id=self._device.resource_id, **data)