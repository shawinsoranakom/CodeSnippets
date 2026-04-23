async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""

        # Remember last color and brightness to restore it when turning on,
        # only if we're sure the light is turned on to avoid overwriting good values
        if self._last_brightness is None:
            self._last_brightness = self.brightness
        if self._current_color and isinstance(self._current_color.value, dict):
            red = self._current_color.value.get(COLOR_SWITCH_COMBINED_RED)
            green = self._current_color.value.get(COLOR_SWITCH_COMBINED_GREEN)
            blue = self._current_color.value.get(COLOR_SWITCH_COMBINED_BLUE)

            last_color: dict[ColorComponent, int] = {}
            if red is not None:
                last_color[ColorComponent.RED] = red
            if green is not None:
                last_color[ColorComponent.GREEN] = green
            if blue is not None:
                last_color[ColorComponent.BLUE] = blue

            # Only store the last color if we're aware of it, i.e. ignore off light
            if last_color and max(last_color.values()) > 0:
                self._last_on_color = last_color

        if self._target_brightness:
            # Turn off the binary switch only
            await self._async_set_brightness(0, kwargs.get(ATTR_TRANSITION))
        else:
            # turn off all color channels
            colors = {
                ColorComponent.RED: 0,
                ColorComponent.GREEN: 0,
                ColorComponent.BLUE: 0,
            }

            await self._async_set_colors(
                colors,
                kwargs.get(ATTR_TRANSITION),
            )