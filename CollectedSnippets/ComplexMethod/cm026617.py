async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on or control the light."""
        commands = self._switch_wrapper.get_update_commands(self.device, True)

        if self._color_mode_wrapper and (
            ATTR_WHITE in kwargs or ATTR_COLOR_TEMP_KELVIN in kwargs
        ):
            commands.extend(
                self._color_mode_wrapper.get_update_commands(
                    self.device, WorkMode.WHITE
                ),
            )

        if self._color_temp_wrapper and ATTR_COLOR_TEMP_KELVIN in kwargs:
            commands.extend(
                self._color_temp_wrapper.get_update_commands(
                    self.device, kwargs[ATTR_COLOR_TEMP_KELVIN]
                )
            )

        if self._color_data_wrapper and (
            ATTR_HS_COLOR in kwargs
            or (
                ATTR_BRIGHTNESS in kwargs
                and self.color_mode == ColorMode.HS
                and ATTR_WHITE not in kwargs
                and ATTR_COLOR_TEMP_KELVIN not in kwargs
            )
        ):
            if self._color_mode_wrapper:
                commands.extend(
                    self._color_mode_wrapper.get_update_commands(
                        self.device, WorkMode.COLOUR
                    ),
                )

            if not (brightness := kwargs.get(ATTR_BRIGHTNESS)):
                brightness = self.brightness or 0

            if not (color := kwargs.get(ATTR_HS_COLOR)):
                color = self.hs_color or (0, 0)

            commands.extend(
                self._color_data_wrapper.get_update_commands(
                    self.device, (color[0], color[1], brightness)
                ),
            )

        elif self._brightness_wrapper and (
            ATTR_BRIGHTNESS in kwargs or ATTR_WHITE in kwargs
        ):
            if ATTR_BRIGHTNESS in kwargs:
                brightness = kwargs[ATTR_BRIGHTNESS]
            else:
                brightness = kwargs[ATTR_WHITE]

            commands.extend(
                self._brightness_wrapper.get_update_commands(self.device, brightness),
            )

        await self._async_send_commands(commands)