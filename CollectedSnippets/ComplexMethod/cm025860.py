def state_attributes(self) -> dict[str, Any] | None:
        """Return state attributes."""
        data: dict[str, Any] = {}
        supported_features = self.supported_features
        supported_color_modes = self._light_internal_supported_color_modes

        _is_on = self.is_on
        color_mode = self.color_mode if _is_on else None
        if _is_on and color_mode is None:
            raise HomeAssistantError(
                f"{self.entity_id} ({type(self)}) does not report a color mode"
            )

        effect: str | None = None
        if LightEntityFeature.EFFECT in supported_features:
            if _is_on:
                effect = self.effect
            data[ATTR_EFFECT] = effect

        self.__validate_color_mode(color_mode, supported_color_modes, effect)

        data[ATTR_COLOR_MODE] = color_mode

        if brightness_supported(supported_color_modes):
            if color_mode in COLOR_MODES_BRIGHTNESS:
                data[ATTR_BRIGHTNESS] = self.brightness
            else:
                data[ATTR_BRIGHTNESS] = None

        if color_temp_supported(supported_color_modes):
            if color_mode == ColorMode.COLOR_TEMP:
                data[ATTR_COLOR_TEMP_KELVIN] = self.color_temp_kelvin
            else:
                data[ATTR_COLOR_TEMP_KELVIN] = None

        if color_supported(supported_color_modes) or color_temp_supported(
            supported_color_modes
        ):
            data[ATTR_HS_COLOR] = None
            data[ATTR_RGB_COLOR] = None
            data[ATTR_XY_COLOR] = None
            if ColorMode.RGBW in supported_color_modes:
                data[ATTR_RGBW_COLOR] = None
            if ColorMode.RGBWW in supported_color_modes:
                data[ATTR_RGBWW_COLOR] = None
            if color_mode:
                data.update(self._light_internal_convert_color(color_mode))

        return data