def _on_static_info_update(self, static_info: EntityInfo) -> None:
        """Set attrs from static info."""
        super()._on_static_info_update(static_info)
        static_info = self._static_info
        self._supports_color_mode = self._api_version >= APIVersion(1, 6)
        self._native_supported_color_modes = tuple(
            static_info.supported_color_modes_compat(self._api_version)
        )
        flags = LightEntityFeature.FLASH

        # All color modes except UNKNOWN,ON_OFF support transition
        modes = self._native_supported_color_modes
        if any(m not in (0, LightColorCapability.ON_OFF) for m in modes):
            flags |= LightEntityFeature.TRANSITION
        if static_info.effects:
            flags |= LightEntityFeature.EFFECT
        self._attr_supported_features = flags

        supported = set(map(_color_mode_to_ha, self._native_supported_color_modes))

        # If we don't know the supported color modes, ESPHome lights
        # are always at least ONOFF so we can safely discard UNKNOWN
        supported.discard(ColorMode.UNKNOWN)

        if ColorMode.ONOFF in supported and len(supported) > 1:
            supported.remove(ColorMode.ONOFF)
        if ColorMode.BRIGHTNESS in supported and len(supported) > 1:
            supported.remove(ColorMode.BRIGHTNESS)
        if ColorMode.WHITE in supported and len(supported) == 1:
            supported.remove(ColorMode.WHITE)

        # If we don't know the supported color modes, its a very old
        # legacy device, and since ESPHome lights are always at least ONOFF
        # we can safely assume that it supports ONOFF
        if not supported:
            supported.add(ColorMode.ONOFF)

        self._attr_supported_color_modes = supported
        self._attr_effect_list = static_info.effects
        self._attr_min_color_temp_kelvin = _mired_to_kelvin(static_info.max_mireds)
        self._attr_max_color_temp_kelvin = _mired_to_kelvin(static_info.min_mireds)