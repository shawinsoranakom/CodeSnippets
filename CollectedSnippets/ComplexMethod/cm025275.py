async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        if not self._device_control:
            return
        transition_time = None
        if ATTR_TRANSITION in kwargs:
            transition_time = int(kwargs[ATTR_TRANSITION]) * 10

        dimmer_command = None
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            brightness = min(brightness, 254)
            dimmer_data = {
                "dimmer": brightness,
                "transition_time": transition_time,
            }
            dimmer_command = self._device_control.set_dimmer(**dimmer_data)
            transition_time = None
        else:
            dimmer_command = self._device_control.set_state(True)

        color_command = None
        if ATTR_HS_COLOR in kwargs and self._device_control.can_set_color:
            hue = int(kwargs[ATTR_HS_COLOR][0] * (self._device_control.max_hue / 360))
            sat = int(
                kwargs[ATTR_HS_COLOR][1] * (self._device_control.max_saturation / 100)
            )
            color_data = {
                "hue": hue,
                "saturation": sat,
                "transition_time": transition_time,
            }
            color_command = self._device_control.set_hsb(**color_data)
            transition_time = None

        temp_command = None
        if ATTR_COLOR_TEMP_KELVIN in kwargs and (
            self._device_control.can_set_temp or self._device_control.can_set_color
        ):
            temp_k = kwargs[ATTR_COLOR_TEMP_KELVIN]
            # White Spectrum bulb
            if self._device_control.can_set_temp:
                temp = color_util.color_temperature_kelvin_to_mired(temp_k)
                if temp < (min_mireds := self._device_control.min_mireds):
                    temp = min_mireds
                elif temp > (max_mireds := self._device_control.max_mireds):
                    temp = max_mireds
                temp_data = {
                    "color_temp": temp,
                    "transition_time": transition_time,
                }
                temp_command = self._device_control.set_color_temp(**temp_data)
                transition_time = None
            # Color bulb (CWS)
            # color_temp needs to be set with hue/saturation
            elif self._device_control.can_set_color:
                hs_color = color_util.color_temperature_to_hs(temp_k)
                hue = int(hs_color[0] * (self._device_control.max_hue / 360))
                sat = int(hs_color[1] * (self._device_control.max_saturation / 100))
                color_data = {
                    "hue": hue,
                    "saturation": sat,
                    "transition_time": transition_time,
                }
                color_command = self._device_control.set_hsb(**color_data)
                transition_time = None

        # HSB can always be set, but color temp + brightness is bulb dependent
        if (command := dimmer_command) is not None:
            command += color_command
        else:
            command = color_command

        if self._device_control.can_combine_commands:
            await self._api(command + temp_command)
        else:
            if temp_command is not None:
                await self._api(temp_command)
            if command is not None:
                await self._api(command)