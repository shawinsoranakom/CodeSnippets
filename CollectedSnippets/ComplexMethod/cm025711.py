async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn light on."""

        hs_color = kwargs.get(ATTR_HS_COLOR)
        xy_color = kwargs.get(ATTR_XY_COLOR)
        color_temp_kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        transition = kwargs.get(ATTR_TRANSITION, 0)
        if self._transitions_disabled:
            transition = 0

        if self.supported_color_modes is not None:
            if hs_color is not None and ColorMode.HS in self.supported_color_modes:
                await self._set_hs_color(hs_color, transition)
            elif xy_color is not None and ColorMode.XY in self.supported_color_modes:
                await self._set_xy_color(xy_color, transition)
            elif (
                color_temp_kelvin is not None
                and ColorMode.COLOR_TEMP in self.supported_color_modes
            ):
                await self._set_color_temp(color_temp_kelvin, transition)

        if brightness is not None and self._supports_brightness:
            await self._set_brightness(brightness, transition)
            return

        await self.send_device_command(
            clusters.OnOff.Commands.On(),
        )