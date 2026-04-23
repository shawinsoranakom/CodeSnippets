async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        mode = None
        if ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            if self._attr_effect_list is None or effect not in self._attr_effect_list:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="unsupported_effect",
                    translation_placeholders={
                        "effect": effect,
                        "device_name": self.device.name,
                    },
                )
            if effect == EFFECT_OFF:
                mode = self._preferred_no_effect_mode
            else:
                mode = self._effect_to_mode[effect]
        elif self._mode is None or (
            self._attr_rgb_color is None and self._attr_brightness is None
        ):
            # Restore previous mode when turning on from Off mode or black color
            mode = self._previous_mode or self._preferred_no_effect_mode

        # Check if current or new mode supports colors
        if mode is None:
            # When not applying a new mode, check if the current mode supports color
            mode_supports_color = self._mode in self._supports_color_modes
        else:
            mode_supports_color = mode in self._supports_color_modes

        color_or_brightness_requested = (
            ATTR_RGB_COLOR in kwargs or ATTR_BRIGHTNESS in kwargs
        )
        if color_or_brightness_requested and not mode_supports_color:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="effect_no_color_support",
                translation_placeholders={
                    "effect": slugify(mode or self._mode or ""),
                    "device_name": self.device.name,
                },
            )

        # Apply color even if switching from Off mode to a color-capable mode
        # because there is no guarantee that the device won't go back to black
        need_to_apply_color = color_or_brightness_requested or (
            mode_supports_color
            and (self._attr_brightness is None or self._attr_rgb_color is None)
        )

        # If color/brightness restoration require color support but mode doesn't support it,
        # switch to a color-capable mode
        if need_to_apply_color and not mode_supports_color:
            mode = self._preferred_no_effect_mode

        if mode is not None:
            await self._async_apply_mode(mode)

        if need_to_apply_color:
            brightness = None
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
            elif self._attr_brightness is None:
                # Restore previous brightness when turning on
                brightness = self._previous_brightness
            if brightness is None:
                # Retain current brightness or use default if still None
                brightness = self._attr_brightness or DEFAULT_BRIGHTNESS

            color = None
            if ATTR_RGB_COLOR in kwargs:
                color = kwargs[ATTR_RGB_COLOR]
            elif self._attr_rgb_color is None:
                # Restore previous color when turning on
                color = self._previous_rgb_color
            if color is None:
                # Retain current color or use default if still None
                color = self._attr_rgb_color or DEFAULT_COLOR

            await self._async_apply_color(color, brightness)

        await self._async_refresh_data()