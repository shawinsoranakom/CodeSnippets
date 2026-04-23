def _get_new_colors(
        self,
        hs_color: tuple[float, float] | None,
        color_temp_k: int | None,
        rgbw: tuple[int, int, int, int] | None,
        brightness_scale: float | None = None,
    ) -> dict[ColorComponent, int] | None:
        """Determine the new color dict to set."""

        # RGB/HS color
        if hs_color is not None and self._supports_color:
            red, green, blue = color_util.color_hs_to_RGB(*hs_color)
            if brightness_scale is not None:
                red = round(red * brightness_scale)
                green = round(green * brightness_scale)
                blue = round(blue * brightness_scale)
            colors = {
                ColorComponent.RED: red,
                ColorComponent.GREEN: green,
                ColorComponent.BLUE: blue,
            }
            if self._supports_color_temp:
                # turn of white leds when setting rgb
                colors[ColorComponent.WARM_WHITE] = 0
                colors[ColorComponent.COLD_WHITE] = 0
            return colors

        # Color temperature
        if color_temp_k is not None and self._supports_color_temp:
            # Limit color temp to min/max values
            color_temp = color_util.color_temperature_kelvin_to_mired(color_temp_k)
            cold = max(
                0,
                min(
                    255,
                    round((MAX_MIREDS - color_temp) / (MAX_MIREDS - MIN_MIREDS) * 255),
                ),
            )
            warm = 255 - cold
            colors = {
                ColorComponent.WARM_WHITE: warm,
                ColorComponent.COLD_WHITE: cold,
            }
            if self._supports_color:
                # turn off color leds when setting color temperature
                colors[ColorComponent.RED] = 0
                colors[ColorComponent.GREEN] = 0
                colors[ColorComponent.BLUE] = 0
            return colors

        # RGBW
        if rgbw is not None and self._supports_rgbw:
            rgbw_channels = {
                ColorComponent.RED: rgbw[0],
                ColorComponent.GREEN: rgbw[1],
                ColorComponent.BLUE: rgbw[2],
            }
            if self._warm_white:
                rgbw_channels[ColorComponent.WARM_WHITE] = rgbw[3]

            if self._cold_white:
                rgbw_channels[ColorComponent.COLD_WHITE] = rgbw[3]

            return rgbw_channels

        return None