async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        # LightEntity color translation will ensure that only attributes of supported
        # color modes are passed to this method - so we can't set unsupported mode here
        if color_temp := kwargs.get(ATTR_COLOR_TEMP_KELVIN):
            self._attr_color_mode = ColorMode.COLOR_TEMP
        if rgb := kwargs.get(ATTR_RGB_COLOR):
            self._attr_color_mode = ColorMode.RGB
        if rgbw := kwargs.get(ATTR_RGBW_COLOR):
            self._attr_color_mode = ColorMode.RGBW
        if hs_color := kwargs.get(ATTR_HS_COLOR):
            self._attr_color_mode = ColorMode.HS
        if xy_color := kwargs.get(ATTR_XY_COLOR):
            self._attr_color_mode = ColorMode.XY

        if (
            not self.is_on
            and brightness is None
            and color_temp is None
            and rgb is None
            and rgbw is None
            and hs_color is None
            and xy_color is None
        ):
            await self._device.set_on()
            return

        async def set_color(
            rgb: tuple[int, int, int], white: int | None, brightness: int | None
        ) -> None:
            """Set color of light. Normalize colors for brightness when not writable."""
            if self._device.brightness.writable:
                # let the KNX light controller handle brightness
                await self._device.set_color(rgb, white)
                if brightness:
                    await self._device.set_brightness(brightness)
                return

            if brightness is None:
                # normalize for brightness if brightness is derived from color
                brightness = self.brightness or 255
            rgb = cast(
                tuple[int, int, int],
                tuple(color * brightness // 255 for color in rgb),
            )
            white = white * brightness // 255 if white is not None else None
            await self._device.set_color(rgb, white)

        # return after RGB(W) color has changed as it implicitly sets the brightness
        if rgbw is not None:
            await set_color(rgbw[:3], rgbw[3], brightness)
            return
        if rgb is not None:
            await set_color(rgb, None, brightness)
            return

        if color_temp is not None:
            color_temp = min(
                self._attr_max_color_temp_kelvin,
                max(self._attr_min_color_temp_kelvin, color_temp),
            )
            if self._device.supports_color_temperature:
                await self._device.set_color_temperature(color_temp)
            elif self._device.supports_tunable_white:
                relative_ct = round(
                    255
                    * (color_temp - self._attr_min_color_temp_kelvin)
                    / (
                        self._attr_max_color_temp_kelvin
                        - self._attr_min_color_temp_kelvin
                    )
                )
                await self._device.set_tunable_white(relative_ct)

        if xy_color is not None:
            await self._device.set_xyy_color(
                XYYColor(color=xy_color, brightness=brightness)
            )
            return

        if hs_color is not None:
            # round so only one telegram will be sent if the other matches state
            hue = round(hs_color[0])
            sat = round(hs_color[1])
            await self._device.set_hs_color((hue, sat))

        if brightness is not None:
            # brightness: 1..255; 0 brightness will call async_turn_off()
            if self._device.brightness.writable:
                await self._device.set_brightness(brightness)
                return
            # brightness without color in kwargs; set via color
            if self._attr_color_mode == ColorMode.XY:
                await self._device.set_xyy_color(XYYColor(brightness=brightness))
                return
            # default to white if color not known for RGB(W)
            if self._attr_color_mode == ColorMode.RGBW:
                _rgbw = self.rgbw_color
                if not _rgbw or not any(_rgbw):
                    _rgbw = (0, 0, 0, 255)
                await set_color(_rgbw[:3], _rgbw[3], brightness)
                return
            if self._attr_color_mode == ColorMode.RGB:
                _rgb = self.rgb_color
                if not _rgb or not any(_rgb):
                    _rgb = (255, 255, 255)
                await set_color(_rgb, None, brightness)
                return