def set_optimistic_attributes(self, **kwargs) -> bool:
        """Update attributes which should be set optimistically.

        Returns True if any attribute was updated.
        """
        optimistic_set = False
        if self._attr_assumed_state:
            self._attr_is_on = True
            optimistic_set = True

        if CONF_LEVEL not in self._templates and ATTR_BRIGHTNESS in kwargs:
            _LOGGER.debug(
                "Optimistically setting brightness to %s", kwargs[ATTR_BRIGHTNESS]
            )
            self._attr_brightness = kwargs[ATTR_BRIGHTNESS]
            optimistic_set = True

        if CONF_TEMPERATURE not in self._templates and ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._set_optimistic_color(
                "color temperature",
                "_attr_color_temp_kelvin",
                kwargs[ATTR_COLOR_TEMP_KELVIN],
                ColorMode.COLOR_TEMP,
            )
            optimistic_set = True

        if CONF_TEMPERATURE not in self._templates and ATTR_COLOR_TEMP in kwargs:
            self._set_optimistic_color(
                "color temperature",
                "_attr_color_temp_kelvin",
                color_util.color_temperature_mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]),
                ColorMode.COLOR_TEMP,
            )
            optimistic_set = True

        if CONF_HS not in self._templates and ATTR_HS_COLOR in kwargs:
            self._set_optimistic_color(
                "hs color", "_attr_hs_color", kwargs[ATTR_HS_COLOR], ColorMode.HS
            )
            optimistic_set = True

        if CONF_RGB not in self._templates and ATTR_RGB_COLOR in kwargs:
            self._set_optimistic_color(
                "rgb color", "_attr_rgb_color", kwargs[ATTR_RGB_COLOR], ColorMode.RGB
            )
            optimistic_set = True

        if CONF_RGBW not in self._templates and ATTR_RGBW_COLOR in kwargs:
            self._set_optimistic_color(
                "rgbw color",
                "_attr_rgbw_color",
                kwargs[ATTR_RGBW_COLOR],
                ColorMode.RGBW,
            )
            optimistic_set = True

        if CONF_RGBWW not in self._templates and ATTR_RGBWW_COLOR in kwargs:
            self._set_optimistic_color(
                "rgbww color",
                "_attr_rgbww_color",
                kwargs[ATTR_RGBWW_COLOR],
                ColorMode.RGBWW,
            )
            optimistic_set = True

        if optimistic_set and not self._attr_assumed_state:
            # If we are optmistically setting color or level but the state template
            # has not rendered, optimisically set the state to 'on'.
            self._attr_is_on = True

        return optimistic_set