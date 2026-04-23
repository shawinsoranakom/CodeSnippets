def turn_on(self, transition_time: int, pipeline: Pipeline, **kwargs: Any) -> None:
        """Turn on (or adjust property of) a group."""
        # The night effect does not need a turned on light
        if kwargs.get(ATTR_EFFECT) == EFFECT_NIGHT:
            if self.effect_list and EFFECT_NIGHT in self.effect_list:
                pipeline.night_light()
                self._attr_effect = EFFECT_NIGHT
            return

        pipeline.on()

        # Set up transition.
        args = {}
        if self.config[CONF_FADE] and not self.is_on and self.brightness:
            args["brightness"] = self.limitlessled_brightness()

        if ATTR_BRIGHTNESS in kwargs:
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
            args["brightness"] = self.limitlessled_brightness()

        if ATTR_HS_COLOR in kwargs:
            self._attr_hs_color = kwargs[ATTR_HS_COLOR]
            # White is a special case.
            assert self.hs_color is not None
            if self.hs_color[1] < MIN_SATURATION:
                pipeline.white()
                self._attr_hs_color = WHITE
            else:
                args["color"] = self.limitlessled_color()

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            assert self.supported_color_modes
            if ColorMode.HS in self.supported_color_modes:
                pipeline.white()
            self._attr_hs_color = WHITE
            self._attr_color_temp_kelvin = kwargs[ATTR_COLOR_TEMP_KELVIN]
            args["temperature"] = self.limitlessled_temperature()

        if args:
            pipeline.transition(transition_time, **args)

        # Flash.
        if ATTR_FLASH in kwargs and self.supported_features & LightEntityFeature.FLASH:
            duration = 0
            if kwargs[ATTR_FLASH] == FLASH_LONG:
                duration = 1
            pipeline.flash(duration=duration)

        # Add effects.
        if ATTR_EFFECT in kwargs and self.effect_list:
            if kwargs[ATTR_EFFECT] == EFFECT_COLORLOOP:
                self._attr_effect = EFFECT_COLORLOOP
                pipeline.append(COLORLOOP)
            if kwargs[ATTR_EFFECT] == EFFECT_WHITE:
                pipeline.white()
                self._attr_hs_color = WHITE