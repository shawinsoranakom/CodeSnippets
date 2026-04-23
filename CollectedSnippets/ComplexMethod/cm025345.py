async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        if self.block.type == "relay":
            self.control_result = await self.set_state(turn="on")
            self.async_write_ha_state()
            return

        set_mode = None
        supported_color_modes = self._attr_supported_color_modes
        params: dict[str, Any] = {"turn": "on"}

        if ATTR_TRANSITION in kwargs:
            params["transition"] = min(
                int(kwargs[ATTR_TRANSITION] * 1000), BLOCK_MAX_TRANSITION_TIME_MS
            )

        if ATTR_BRIGHTNESS in kwargs and brightness_supported(supported_color_modes):
            if hasattr(self.block, "gain"):
                params["gain"] = brightness_to_percentage(kwargs[ATTR_BRIGHTNESS])
            if hasattr(self.block, "brightness"):
                params["brightness"] = brightness_to_percentage(kwargs[ATTR_BRIGHTNESS])

        if (
            ATTR_COLOR_TEMP_KELVIN in kwargs
            and ColorMode.COLOR_TEMP in supported_color_modes
        ):
            # Color temperature change - used only in white mode,
            # switch device mode to white
            color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]
            set_mode = "white"
            params["temp"] = int(
                min(
                    self.max_color_temp_kelvin,
                    max(self.min_color_temp_kelvin, color_temp),
                )
            )

        if ATTR_RGB_COLOR in kwargs and ColorMode.RGB in supported_color_modes:
            # Color channels change - used only in color mode,
            # switch device mode to color
            set_mode = "color"
            (params["red"], params["green"], params["blue"]) = kwargs[ATTR_RGB_COLOR]

        if ATTR_RGBW_COLOR in kwargs and ColorMode.RGBW in supported_color_modes:
            # Color channels change - used only in color mode,
            # switch device mode to color
            set_mode = "color"
            (params["red"], params["green"], params["blue"], params["white"]) = kwargs[
                ATTR_RGBW_COLOR
            ]

        if ATTR_EFFECT in kwargs and ATTR_COLOR_TEMP_KELVIN not in kwargs:
            # Color effect change - used only in color mode, switch device mode to color
            set_mode = "color"
            if self.coordinator.model == MODEL_BULB:
                effect_dict = SHBLB_1_RGB_EFFECTS
            else:
                effect_dict = STANDARD_RGB_EFFECTS
            if kwargs[ATTR_EFFECT] in effect_dict.values():
                params["effect"] = [
                    k for k, v in effect_dict.items() if v == kwargs[ATTR_EFFECT]
                ][0]
            else:
                LOGGER.error(
                    "Effect '%s' not supported by device %s",
                    kwargs[ATTR_EFFECT],
                    self.coordinator.model,
                )

        if (
            set_mode
            and set_mode != self.mode
            and self.coordinator.model in DUAL_MODE_LIGHT_MODELS
        ):
            params["mode"] = set_mode

        self.control_result = await self.set_state(**params)
        self.async_write_ha_state()