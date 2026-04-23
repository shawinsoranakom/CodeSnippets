async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            color_temp = color_util.color_temperature_kelvin_to_mired(
                kwargs[ATTR_COLOR_TEMP_KELVIN]
            )
            percent_color_temp = self.translate(
                color_temp, self._max_mireds, self._min_mireds, CCT_MIN, CCT_MAX
            )

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            percent_brightness = ceil(100 * brightness / 255.0)

        if ATTR_BRIGHTNESS in kwargs and ATTR_COLOR_TEMP_KELVIN in kwargs:
            _LOGGER.debug(
                "Setting brightness and color temperature: %s %s%%, %s mireds, %s%% cct",
                brightness,
                percent_brightness,
                color_temp,
                percent_color_temp,
            )

            result = await self._try_command(
                "Setting brightness and color temperature failed: %s bri, %s cct",
                self._device.set_brightness_and_color_temperature,
                percent_brightness,
                percent_color_temp,
            )

            if result:
                self._color_temp = color_temp
                self._attr_brightness = brightness

        elif ATTR_COLOR_TEMP_KELVIN in kwargs:
            _LOGGER.debug(
                "Setting color temperature: %s mireds, %s%% cct",
                color_temp,
                percent_color_temp,
            )

            result = await self._try_command(
                "Setting color temperature failed: %s cct",
                self._device.set_color_temperature,
                percent_color_temp,
            )

            if result:
                self._color_temp = color_temp

        elif ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            percent_brightness = ceil(100 * brightness / 255.0)

            _LOGGER.debug("Setting brightness: %s %s%%", brightness, percent_brightness)

            result = await self._try_command(
                "Setting brightness failed: %s",
                self._device.set_brightness,
                percent_brightness,
            )

            if result:
                self._attr_brightness = brightness

        else:
            await self._try_command("Turning the light on failed.", self._device.on)