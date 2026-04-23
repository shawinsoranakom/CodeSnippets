def turn_on(self, **kwargs: Any) -> None:
        """Turn the light on and/or change color or color effect settings."""
        if ATTR_TRANSITION in kwargs:
            self._hmdevice.setValue("RAMP_TIME", kwargs[ATTR_TRANSITION], self._channel)

        if ATTR_BRIGHTNESS in kwargs and self._state == "LEVEL":
            percent_bright = float(kwargs[ATTR_BRIGHTNESS]) / 255
            self._hmdevice.set_level(percent_bright, self._channel)
        elif (
            ATTR_HS_COLOR not in kwargs
            and ATTR_COLOR_TEMP_KELVIN not in kwargs
            and ATTR_EFFECT not in kwargs
        ):
            self._hmdevice.on(self._channel)

        if ATTR_HS_COLOR in kwargs:
            self._hmdevice.set_hs_color(
                hue=kwargs[ATTR_HS_COLOR][0] / 360.0,
                saturation=kwargs[ATTR_HS_COLOR][1] / 100.0,
                channel=self._channel,
            )
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            mireds = color_util.color_temperature_kelvin_to_mired(
                kwargs[ATTR_COLOR_TEMP_KELVIN]
            )
            hm_temp = (MAX_MIREDS - mireds) / (MAX_MIREDS - MIN_MIREDS)
            self._hmdevice.set_color_temp(hm_temp)
        if ATTR_EFFECT in kwargs:
            self._hmdevice.set_effect(kwargs[ATTR_EFFECT])