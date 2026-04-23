def _light_internal_convert_color(
        self, color_mode: ColorMode | str
    ) -> dict[str, tuple[float, ...]]:
        data: dict[str, tuple[float, ...]] = {}
        if color_mode == ColorMode.HS and (hs_color := self.hs_color):
            data[ATTR_HS_COLOR] = (round(hs_color[0], 3), round(hs_color[1], 3))
            data[ATTR_RGB_COLOR] = color_util.color_hs_to_RGB(*hs_color)
            data[ATTR_XY_COLOR] = color_util.color_hs_to_xy(*hs_color)
        elif color_mode == ColorMode.XY and (xy_color := self.xy_color):
            data[ATTR_HS_COLOR] = color_util.color_xy_to_hs(*xy_color)
            data[ATTR_RGB_COLOR] = color_util.color_xy_to_RGB(*xy_color)
            data[ATTR_XY_COLOR] = (round(xy_color[0], 6), round(xy_color[1], 6))
        elif color_mode == ColorMode.RGB and (rgb_color := self.rgb_color):
            data[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
            data[ATTR_RGB_COLOR] = tuple(int(x) for x in rgb_color[0:3])
            data[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif color_mode == ColorMode.RGBW and (
            rgbw_color := self._light_internal_rgbw_color
        ):
            rgb_color = color_util.color_rgbw_to_rgb(*rgbw_color)
            data[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
            data[ATTR_RGB_COLOR] = tuple(int(x) for x in rgb_color[0:3])
            data[ATTR_RGBW_COLOR] = tuple(int(x) for x in rgbw_color[0:4])
            data[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif color_mode == ColorMode.RGBWW and (rgbww_color := self.rgbww_color):
            rgb_color = color_util.color_rgbww_to_rgb(
                *rgbww_color, self.min_color_temp_kelvin, self.max_color_temp_kelvin
            )
            data[ATTR_HS_COLOR] = color_util.color_RGB_to_hs(*rgb_color)
            data[ATTR_RGB_COLOR] = tuple(int(x) for x in rgb_color[0:3])
            data[ATTR_RGBWW_COLOR] = tuple(int(x) for x in rgbww_color[0:5])
            data[ATTR_XY_COLOR] = color_util.color_RGB_to_xy(*rgb_color)
        elif color_mode == ColorMode.COLOR_TEMP and (
            color_temp_kelvin := self.color_temp_kelvin
        ):
            hs_color = color_util.color_temperature_to_hs(color_temp_kelvin)
            data[ATTR_HS_COLOR] = (round(hs_color[0], 3), round(hs_color[1], 3))
            data[ATTR_RGB_COLOR] = color_util.color_hs_to_RGB(*hs_color)
            data[ATTR_XY_COLOR] = color_util.color_hs_to_xy(*hs_color)
        return data