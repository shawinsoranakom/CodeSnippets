def __init__(self, group: Group, config: dict[str, Any]) -> None:
        """Initialize a group."""

        if isinstance(group, WhiteGroup):
            self._attr_supported_color_modes = COLOR_MODES_LIMITLESS_WHITE
            self._attr_supported_features = SUPPORT_LIMITLESSLED_WHITE
            self._attr_effect_list = [EFFECT_NIGHT]
        elif isinstance(group, DimmerGroup):
            self._attr_supported_color_modes = COLOR_MODES_LIMITLESS_DIMMER
            self._attr_supported_features = SUPPORT_LIMITLESSLED_DIMMER
            self._attr_effect_list = []
        elif isinstance(group, RgbwGroup):
            self._attr_supported_color_modes = COLOR_MODES_LIMITLESS_RGB
            self._attr_supported_features = SUPPORT_LIMITLESSLED_RGB
            self._attr_effect_list = [EFFECT_COLORLOOP, EFFECT_NIGHT, EFFECT_WHITE]
        elif isinstance(group, RgbwwGroup):
            self._attr_supported_color_modes = COLOR_MODES_LIMITLESS_RGBWW
            self._attr_supported_features = SUPPORT_LIMITLESSLED_RGBWW
            self._attr_effect_list = [EFFECT_COLORLOOP, EFFECT_NIGHT, EFFECT_WHITE]

        self._fixed_color_mode = None
        if self.supported_color_modes and len(self.supported_color_modes) == 1:
            self._fixed_color_mode = next(iter(self.supported_color_modes))
        else:
            assert self._attr_supported_color_modes == {
                ColorMode.COLOR_TEMP,
                ColorMode.HS,
            }

        self.led_group = group
        self._attr_name = group.name
        self.config = config
        self._attr_is_on = False