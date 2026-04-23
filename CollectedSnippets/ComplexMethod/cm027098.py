def _setup_from_entity(self) -> None:
        """(Re)Setup the entity."""
        self._attr_supported_color_modes = set()
        supported_features = LightEntityFeature(0)
        light_type = self._tasmota_entity.light_type

        if light_type in [LIGHT_TYPE_RGB, LIGHT_TYPE_RGBW, LIGHT_TYPE_RGBCW]:
            # Mark HS support for RGBW light because we don't have direct
            # control over the white channel, so the base component's RGB->RGBW
            # translation does not work
            self._attr_supported_color_modes.add(ColorMode.HS)
            self._attr_color_mode = ColorMode.HS

        if light_type == LIGHT_TYPE_RGBW:
            self._attr_supported_color_modes.add(ColorMode.WHITE)

        if light_type in [LIGHT_TYPE_COLDWARM, LIGHT_TYPE_RGBCW]:
            self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
            self._attr_color_mode = ColorMode.COLOR_TEMP

        if light_type != LIGHT_TYPE_NONE and not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
            self._attr_color_mode = ColorMode.BRIGHTNESS

        if not self._attr_supported_color_modes:
            self._attr_supported_color_modes.add(ColorMode.ONOFF)
            self._attr_color_mode = ColorMode.ONOFF

        if light_type in [LIGHT_TYPE_RGB, LIGHT_TYPE_RGBW, LIGHT_TYPE_RGBCW]:
            supported_features |= LightEntityFeature.EFFECT

        if self._tasmota_entity.supports_transition:
            supported_features |= LightEntityFeature.TRANSITION

        self._attr_supported_features = supported_features