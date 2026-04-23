def __init__(self, entity_data: EntityData) -> None:
        """Initialize the ZHA light."""
        super().__init__(entity_data)
        color_modes: set[ColorMode] = set()
        has_brightness = False
        for color_mode in self.entity_data.entity.supported_color_modes:
            if color_mode == ZhaColorMode.BRIGHTNESS:
                has_brightness = True
            if color_mode not in (ZhaColorMode.BRIGHTNESS, ZhaColorMode.ONOFF):
                color_modes.add(ZHA_TO_HA_COLOR_MODE[color_mode])
        if color_modes:
            self._attr_supported_color_modes = color_modes
        elif has_brightness:
            color_modes.add(ColorMode.BRIGHTNESS)
            self._attr_supported_color_modes = color_modes
        else:
            color_modes.add(ColorMode.ONOFF)
            self._attr_supported_color_modes = color_modes

        features = LightEntityFeature(0)
        zha_features: ZhaLightEntityFeature = self.entity_data.entity.supported_features

        if ZhaLightEntityFeature.EFFECT in zha_features:
            features |= LightEntityFeature.EFFECT
        if ZhaLightEntityFeature.FLASH in zha_features:
            features |= LightEntityFeature.FLASH
        if ZhaLightEntityFeature.TRANSITION in zha_features:
            features |= LightEntityFeature.TRANSITION

        self._attr_supported_features = features