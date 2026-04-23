async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        temperature_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        hue = None
        saturation = None
        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]

        brightness = None
        if ATTR_BRIGHTNESS in kwargs:
            brightness = round((kwargs[ATTR_BRIGHTNESS] / 255) * 100)

        # For Elgato lights supporting color mode, but in temperature mode;
        # adjusting only brightness make them jump back to color mode.
        # Resending temperature prevents that.
        if (
            brightness
            and ATTR_HS_COLOR not in kwargs
            and ATTR_COLOR_TEMP_KELVIN not in kwargs
            and self.supported_color_modes
            and ColorMode.HS in self.supported_color_modes
            and self.color_mode == ColorMode.COLOR_TEMP
        ):
            temperature_kelvin = self.color_temp_kelvin

        temperature = (
            None
            if temperature_kelvin is None
            else color_util.color_temperature_kelvin_to_mired(temperature_kelvin)
        )

        await self.coordinator.client.light(
            on=True,
            brightness=brightness,
            hue=hue,
            saturation=saturation,
            temperature=temperature,
        )
        await self.coordinator.async_request_refresh()