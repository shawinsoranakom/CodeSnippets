async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device on."""

        if (
            kwargs.get(ATTR_RGBW_COLOR) is not None
            or kwargs.get(ATTR_COLOR_TEMP_KELVIN) is not None
        ):
            # RGBW and color temp are not supported in this mode,
            # delegate to the parent class
            await super().async_turn_on(**kwargs)
            return

        transition = kwargs.get(ATTR_TRANSITION)
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        hs_color = kwargs.get(ATTR_HS_COLOR)
        new_colors: dict[ColorComponent, int] | None = None
        scale: float | None = None

        if brightness is None and hs_color is None:
            # Turned on without specifying brightness or color
            if self._last_on_color is not None:
                if self._target_brightness:
                    # Color is already set, use the binary switch to turn on
                    await self._async_set_brightness(None, transition)
                    return

                # Preserve the previous color
                new_colors = self._last_on_color
            elif self._supports_color:
                # Turned on for the first time. Make it white
                new_colors = {
                    ColorComponent.RED: 255,
                    ColorComponent.GREEN: 255,
                    ColorComponent.BLUE: 255,
                }
        elif brightness is not None:
            # If brightness gets set, preserve the color and mix it with the new brightness
            if self.color_mode == ColorMode.HS:
                scale = brightness / 255
            if self._last_on_color is not None:
                # Changed brightness from 0 to >0
                old_brightness = max(self._last_on_color.values())
                new_scale = brightness / old_brightness
                scale = new_scale
                new_colors = {}
                for color, value in self._last_on_color.items():
                    new_colors[color] = round(value * new_scale)
            elif hs_color is None and self._attr_color_mode == ColorMode.HS:
                hs_color = self._attr_hs_color
        elif hs_color is not None and brightness is None:
            # Turned on by using the color controls
            current_brightness = self.brightness
            if current_brightness == 0 and self._last_brightness is not None:
                # Use the last brightness value if the light is currently off
                scale = self._last_brightness / 255
            elif current_brightness is not None:
                scale = current_brightness / 255

        # Reset last color and brightness until turning off again
        self._last_on_color = None
        self._last_brightness = None

        if new_colors is None:
            new_colors = self._get_new_colors(
                hs_color=hs_color, color_temp_k=None, rgbw=None, brightness_scale=scale
            )

        if new_colors is not None:
            await self._async_set_colors(new_colors, transition)

        # Turn the binary switch on if there is one
        await self._async_set_brightness(brightness, transition)