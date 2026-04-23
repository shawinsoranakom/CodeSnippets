async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        data: dict[str, Any] = {"key": self._key, "state": True}
        # The list of color modes that would fit this service call
        color_modes = self._native_supported_color_modes
        try_keep_current_mode = True

        # rgb/brightness input is in range 0-255, but esphome uses 0-1

        if (brightness_ha := kwargs.get(ATTR_BRIGHTNESS)) is not None:
            data["brightness"] = brightness_ha / 255
            color_modes = _filter_color_modes(
                color_modes, LightColorCapability.BRIGHTNESS
            )

        if (rgb_ha := kwargs.get(ATTR_RGB_COLOR)) is not None:
            rgb = tuple(x / 255 for x in rgb_ha)
            color_bri = max(rgb)
            # normalize rgb
            data["rgb"] = tuple(x / (color_bri or 1) for x in rgb)
            data["color_brightness"] = color_bri
            color_modes = _filter_color_modes(color_modes, LightColorCapability.RGB)
            try_keep_current_mode = False

        if (rgbw_ha := kwargs.get(ATTR_RGBW_COLOR)) is not None:
            *rgb, w = tuple(x / 255 for x in rgbw_ha)  # type: ignore[assignment]
            color_bri = max(rgb)
            # normalize rgb
            data["rgb"] = tuple(x / (color_bri or 1) for x in rgb)
            data["white"] = w
            data["color_brightness"] = color_bri
            color_modes = _filter_color_modes(
                color_modes, LightColorCapability.RGB | LightColorCapability.WHITE
            )
            try_keep_current_mode = False

        if (rgbww_ha := kwargs.get(ATTR_RGBWW_COLOR)) is not None:
            *rgb, cw, ww = tuple(x / 255 for x in rgbww_ha)  # type: ignore[assignment]
            color_bri = max(rgb)
            # normalize rgb
            data["rgb"] = tuple(x / (color_bri or 1) for x in rgb)
            color_modes = _filter_color_modes(color_modes, LightColorCapability.RGB)
            if _filter_color_modes(color_modes, LightColorCapability.COLD_WARM_WHITE):
                # Device supports setting cwww values directly
                data["cold_white"] = cw
                data["warm_white"] = ww
                color_modes = _filter_color_modes(
                    color_modes, LightColorCapability.COLD_WARM_WHITE
                )
            else:
                # need to convert cw+ww part to white+color_temp
                white = data["white"] = max(cw, ww)
                if white != 0:
                    static_info = self._static_info
                    min_ct = static_info.min_mireds
                    max_ct = static_info.max_mireds
                    ct_ratio = ww / (cw + ww)
                    data["color_temperature"] = min_ct + ct_ratio * (max_ct - min_ct)
                color_modes = _filter_color_modes(
                    color_modes,
                    LightColorCapability.COLOR_TEMPERATURE | LightColorCapability.WHITE,
                )
            try_keep_current_mode = False

            data["color_brightness"] = color_bri

        if (flash := kwargs.get(ATTR_FLASH)) is not None:
            data["flash_length"] = FLASH_LENGTHS[flash]

        if (transition := kwargs.get(ATTR_TRANSITION)) is not None:
            data["transition_length"] = transition

        if (color_temp_k := kwargs.get(ATTR_COLOR_TEMP_KELVIN)) is not None:
            # Do not use kelvin_to_mired here to prevent precision loss
            color_temp_mired = 1_000_000.0 / color_temp_k
            data["color_temperature"] = color_temp_mired
            if color_temp_modes := _filter_color_modes(
                color_modes, LightColorCapability.COLOR_TEMPERATURE
            ):
                color_modes = color_temp_modes
            else:
                # Also send explicit cold/warm white values to avoid
                # ESPHome applying brightness to both master brightness
                # and white channels (b² effect). The firmware skips
                # deriving cwww from color_temperature when the channels
                # are already set explicitly, but still stores
                # color_temperature so HA can read it back.
                data["cold_white"], data["warm_white"] = self._color_temp_to_cold_warm(
                    color_temp_mired
                )
                color_modes = _filter_color_modes(
                    color_modes, LightColorCapability.COLD_WARM_WHITE
                )
            try_keep_current_mode = False

        if (effect := kwargs.get(ATTR_EFFECT)) is not None:
            data["effect"] = effect

        if (white_ha := kwargs.get(ATTR_WHITE)) is not None:
            # ESPHome multiplies brightness and white together for final brightness
            # HA only sends `white` in turn_on, and reads total brightness
            # through brightness property.
            data["brightness"] = white_ha / 255
            data["white"] = 1.0
            color_modes = _filter_color_modes(
                color_modes,
                LightColorCapability.BRIGHTNESS | LightColorCapability.WHITE,
            )
            try_keep_current_mode = False

        if self._supports_color_mode and color_modes:
            if (
                try_keep_current_mode
                and self._state is not None
                and self._state.color_mode in color_modes
            ):
                # if possible, stay with the color mode that is already set
                data["color_mode"] = self._state.color_mode
            else:
                # otherwise try the color mode with the least complexity
                # (fewest capabilities set)
                data["color_mode"] = _least_complex_color_mode(color_modes)

        self._client.light_command(**data, device_id=self._static_info.device_id)